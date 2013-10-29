#!/usr/bin/python
# coding: utf-8

'''Static site generator.'''

from os import path as osp
import argparse
import codecs
import logging
import os
import re
import shutil
import time

from mako.lookup import TemplateLookup
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from lib import Namespace  # pylint: disable=W0403


__author__ = 'The Metaist'
__copyright__ = 'Copyright 2013, Metaist'
__email__ = 'metaist@metaist.com'
__license__ = 'MIT'
__maintainer__ = 'The Metaist'
__status__ = 'Prototype'
__version__ = '0.0.2'
__version_info__ = tuple(__version__.split('.'))


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

RE_MAKO_DEPENDENCY = re.compile(r'<%(include|inherit)\s+file="(.*)"')


class PageitWatcher(FileSystemEventHandler):
    '''Handler for changes to directories.'''
    runner = None

    def __init__(self, runner):
        self.runner = runner

    def on_modified(self, event):
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
            self.process_dir(files, srcpath, destpath, relpath)

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

    def process_dir(self, files, src, dest, relpath):
        '''Process a directory.'''
        prefix = self.args.mako_prefix
        for name in files:
            srcfile = osp.join(src, name)
            destfile = osp.join(dest, name)
            relfile = osp.join(relpath, name)
            process_file = self.copy_file  # copy unless rendering
            change_time = int(osp.getmtime(srcfile))

            if name.startswith(prefix):
                process_file = self.render_file
                destfile = osp.join(dest, name[len(prefix):])
                change_time = self.mako_mtime(srcfile)

            if (not self.args.ignore_mtime and osp.isfile(destfile) and
                    change_time <= int(osp.getmtime(destfile))):
                process_file = self.skip_file  # skip this older file

            process_file(relfile, srcfile, destfile)

        return self

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
        with codecs.open(dest, encoding='utf-8', mode='w') as out:
            rendered = tmpl.render_unicode(site=self.site, page=Namespace())
            out.write(rendered)
        self.logger.info(MSG_RENDER.format(name, src, dest))
        return self

    def mako_mtime(self, path):
        '''Return the latest mtime of a mako template and its dependencies.'''
        path = osp.abspath(path)
        if path in self.mtimes:
            return self.mtimes[path]

        result = int(osp.getmtime(path))
        deps = mako_deps(path)
        mtimes = [result] + [self.mako_mtime(dep) for dep in deps]
        result = max(mtimes)

        self.mtimes[path] = result
        return result


def mako_deps(path):
    '''Returns list of dependencies for a mako template.'''
    results = []
    path = osp.abspath(path)
    pathdir = osp.dirname(path)
    for line in open(path):
        groups = RE_MAKO_DEPENDENCY.search(line)  # look for imports
        if groups:
            dep = osp.abspath(osp.join(pathdir, groups.group(2)))
            if dep not in results:
                results.append(dep)
    return results


def parse_args(args=None):
    '''Parse command-line arguments.

    >>> parse_args(['-o', 'output']) is not None
    True
    '''
    parser = argparse.ArgumentParser(prog='pageit', description=__doc__)
    parser.set_defaults(**DEFAULT_ARGS)  # pylint: disable=W0142
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)

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
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print ''
        observer.join()


if __name__ == '__main__':  # pragma: no cover
    main()
