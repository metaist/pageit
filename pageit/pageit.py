#!/usr/bin/python
# coding: utf-8

'''Static site generator.'''

from os import path as osp
import time
import SocketServer
import SimpleHTTPServer
import shutil
import re
import os
import logging
import codecs
import argparse

from mako.lookup import TemplateLookup
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from lib import Namespace  # pylint: disable=W0403
import __init__ as package  # pylint: disable=W0403

DEFAULT_ARGS = Namespace(
    config='config.yml',
    env='default',
    mako_prefix='mako.',

    src='site',
    dest='output',
    tmp='tmp',

    init=False,
    quiet=False,
    verbose=False,
    watch=False,
    ignore_mtime=False
)

logging.basicConfig(format='%(message)s')
DEFAULT_LOGGER = logging.getLogger('com.metaist.pageit')

MSG_COPY = 'copy   {0}'
MSG_DELETE = 'delete {0}'
MSG_CREATE = 'create {0}'
MSG_RENDER = 'render {0}'
MSG_SKIP = 'skip   {0}'

RE_MAKO_DEPENDENCY = re.compile(
    r'<%(include|inherit|namespace)\s+file="([^"]*)"'
)


class PageitWatcher(FileSystemEventHandler):
    '''Handler for changes to directories.'''
    runner = None

    def __init__(self, runner):
        print '[WATCH] start watching', runner.args.src
        self.runner = runner

    def on_modified(self, event):
        print '[WATCH] file changed', event.src_path
        self.runner.run()


class Pageit(object):
    '''Site generator.'''
    args, site = DEFAULT_ARGS, Namespace()
    logger = DEFAULT_LOGGER
    mtimes = {}

    def __init__(self, args=None, site=None, logger=None):
        '''Construct a generator.

        >>> Pageit() is not None
        True
        '''
        self.logger = logger or self.logger
        self.site += site
        self.args += args
        self.args += Namespace(src=osp.abspath(self.args.src),
                               dest=osp.abspath(self.args.dest))
        args = self.args  # shorthand

        self.logger.setLevel(logging.INFO)
        if args.quiet:
            self.logger.setLevel(logging.NOTSET)
        elif args.verbose:
            self.logger.setLevel(logging.DEBUG)

        if args.init:  # delete existing directories
            for dirname in [args.dest, args.tmp]:
                if osp.isdir(dirname):
                    shutil.rmtree(dirname)
                    self.logger.debug(MSG_DELETE.format(osp.basename(dirname)))

        self._tmpl = TemplateLookup(
            directories=[args.src],
            module_directory=args.tmp,
            input_encoding='utf-8',
            output_encoding='utf-8'
        )

    def run(self, src=None, dest=None):
        '''Generate the site.'''
        src = src or self.args.src
        dest = dest or self.args.dest

        assert osp.isdir(src), 'Cannot find site in {0}'.format(src)

        prefix = self.args.mako_prefix
        for root, _, files in os.walk(src):
            srcpath = osp.abspath(osp.join(src, root))
            relpath = srcpath[len(src) + 1:]

            if osp.basename(srcpath).startswith(prefix):
                self.skip_dir(relpath, srcpath)
                continue  # this directory should not be processed

            destpath = osp.abspath(osp.join(dest, relpath))
            destbase = osp.basename(destpath)
            self.create_dir(relpath or destbase, destpath)  # dir exists
            for name in files:
                self.process_file(name, srcpath, destpath, relpath)

    def skip_dir(self, name, src):
        '''Skip a directory.'''
        self.logger.debug(MSG_SKIP.format(name, src))
        return self

    def create_dir(self, name, dest):
        '''Create a directory.'''
        if not osp.isdir(dest):
            os.mkdir(dest)
            self.logger.info(MSG_CREATE.format(name))
        return self

    def process_file(self, name, src, dest, relpath):
        '''Process a file.'''
        prefix = self.args.mako_prefix
        srcfile = osp.join(src, name)
        destfile = osp.join(dest, name)
        relfile = osp.join(relpath, name)
        file_action = self.copy_file  # copy unless rendering
        change_time = int(osp.getmtime(srcfile))

        if name.startswith(prefix):
            file_action = self.render_file
            destfile = osp.join(dest, name[len(prefix):])
            self.mtimes = {}  # reset mtimes
            change_time = self.mako_mtime(srcfile)

        if (not self.args.ignore_mtime and osp.isfile(destfile) and
                change_time <= int(osp.getmtime(destfile))):
            file_action = self.skip_file  # skip this older file

        file_action(relfile, srcfile, destfile)

    def skip_file(self, name, src, dest):
        '''Skip a file.'''
        self.logger.debug(MSG_SKIP.format(name, src, dest))
        return self

    def copy_file(self, name, src, dest):
        '''Copy a file.'''
        shutil.copy2(src, dest)
        self.logger.info(MSG_COPY.format(name, src, dest))
        return self

    def render_file(self, name, src, dest):
        '''Render a file.'''
        tmpl = self._tmpl.get_template(name)
        try:
            rendered = tmpl.render_unicode(site=self.site, page=Namespace())
            with codecs.open(dest, encoding='utf-8', mode='w') as out:
                out.write(rendered)
            self.logger.info(MSG_RENDER.format(name, src, dest))
        except:
            self.logger.error('Error rendering {0}'.format(name))
            raise

        return self

    def mako_deps(self, path):
        '''Return non-recursive list of dependencies for a mako template.'''
        results = []
        path = osp.abspath(path)
        self.logger.debug('dependencies for {0}'.format(path))
        for line in open(path):
            groups = RE_MAKO_DEPENDENCY.search(line)  # look for imports
            if groups:
                dep = groups.group(2)
                if '/' == dep[0]:  # relative to src
                    dep = osp.normpath(osp.join(self.args.src,
                                                dep.lstrip('/')))
                else:  # relative to current dir
                    dep = osp.normpath(osp.join(osp.dirname(path), dep))

                if dep not in results:
                    self.logger.debug('depends on {0}'.format(dep))
                    results.append(dep)
        return results

    def mako_mtime(self, path):
        '''Return the latest mtime of a mako template and its dependencies.'''
        self.logger.debug('last mtime for {0}'.format(path))
        if path in self.mtimes:
            return self.mtimes[path]

        result = int(osp.getmtime(path))
        deps = self.mako_deps(path)
        mtimes = [result] + [self.mako_mtime(dep) for dep in deps]
        result = max(mtimes)

        self.mtimes[path] = result
        return result


def parse_args(args=None):
    '''Parse command-line arguments.

    >>> parse_args(['-o', 'output']) is not None
    True
    '''
    parser = argparse.ArgumentParser(prog='pageit', description=__doc__)
    parser.set_defaults(**DEFAULT_ARGS)  # pylint: disable=W0142
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + package.__version__)

    group = parser.add_argument_group('configuration')
    group.add_argument('-f', '--config', metavar='FILE',
                       help='parse config file (default: "%(default)s")')
    group.add_argument('-e', '--env', metavar='ENV',
                       help='config environment (default: "%(default)s")')
    group.add_argument('--mako-prefix', metavar='STR',
                       help='mako prefix (default: "%(default)s")')

    group = parser.add_argument_group('directories')
    group.add_argument('-s', '--src', metavar='PATH',
                       help='source dir (default: "%(default)s")')
    group.add_argument('-o', '--dest', metavar='PATH',
                       help='output dir (default: "%(default)s")')
    group.add_argument('-t', '--tmp', metavar='PATH',
                       help='temp dir (default: "%(default)s")')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', action='store_true',
                       help='verbose (default: %(default)s)')
    group.add_argument('-q', '--quiet', action='store_true',
                       help='quiet (default: %(default)s)')

    group = parser.add_argument_group('switches')
    group.add_argument('-i', '--init', action='store_true',
                       help='delete existing outputs (default: %(default)s)')
    group.add_argument('-w', '--watch', action='store_true',
                       help='watch for changes (default: %(default)s)')
    group.add_argument('--serve', nargs='?', metavar='PORT', const=80,
                       help='run simple HTTP server (default: %(default)s)')
    group.add_argument('--ignore-mtime', action='store_true',
                       help='ignore timestamps (default: %(default)s)')

    return parser.parse_args(args)


def parse_config(path, env='default'):
    '''Parse site configuration file.'''
    assert osp.isfile(path), 'Invalid path: {0}'.format(path)

    site = yaml.load(open(path, 'r'))
    assert 'default' in site, 'Configuration must have [default] section.'
    result = Namespace(**site['default'])  # pylint: disable=W0142

    if env != 'default' and env in site:
        result += site[env]

    return result


def start_server(path, port=80):
    '''Start the server.'''
    os.chdir(path)
    handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(("", int(port)), handler)
    print '[SERVE] start serving on port', port
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print '[SERVE] stopping server'


def main(args=None):  # pragma: no cover
    '''Main entry point.'''
    args = parse_args(args)
    site = Namespace()
    if osp.isfile(args.config):
        site = parse_config(args.config, args.env)
    runner = Pageit(args, site)
    runner.run()  # run once

    if args.watch:  # watch for changes
        handler = PageitWatcher(runner)
        observer = Observer()
        observer.schedule(handler, path=args.src, recursive=True)
        observer.start()
        if args.serve:
            start_server(args.dest, args.serve)
            observer.stop()
        else:
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
                print ''
        observer.join()
    elif args.serve:
        start_server(args.dest, args.serve)


if __name__ == '__main__':  # pragma: no cover
    main()
