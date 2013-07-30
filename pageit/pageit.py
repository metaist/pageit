#!/usr/bin/python
# coding: utf-8

'''Static site generator.'''

from os import path as osp
import argparse
import codecs
import os
import shutil

from mako.lookup import TemplateLookup
import yaml

from lib import Namespace  # pylint: disable=W0403


__author__ = 'The Metaist'
__copyright__ = 'Copyright 2013, Metaist'
__email__ = 'metaist@metaist.com'
__license__ = 'MIT'
__maintainer__ = 'The Metaist'
__status__ = 'Prototype'
__version__ = '0.0.1'
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
    ignore_mtime=False
)


class Pageit(object):
    '''Site generator.'''
    MSG_COPYFILE = 'copy   {0}'
    MSG_DELDIR = 'delete {0}'
    MSG_NEWDIR = 'create {0}'
    MSG_RENDERED = 'render {0}'
    MSG_SKIPDIR = 'skip   {0}'
    MSG_SKIPFILE = 'skip   {0}'

    args, site = DEFAULT_ARGS, Namespace()

    def __init__(self, args=None, site=None):
        '''Construct a generator.

        >>> Pageit() is not None
        True
        '''
        self.site += site
        self.args += args
        self.args += Namespace(src=osp.abspath(self.args.src),
                               dest=osp.abspath(self.args.dest))
        args = self.args  # shorthand

        if args.init:  # delete existing directories
            for dirname in [args.dest, args.tmp]:
                if osp.isdir(dirname):
                    shutil.rmtree(dirname)
                    print self.MSG_DELDIR.format(osp.basename(dirname))

        self._tmpl = TemplateLookup(directories=[args.src],
                                    module_directory=args.tmp,
                                    input_encoding='utf-8',
                                    output_encoding='utf-8')

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
        print self.MSG_SKIPDIR.format(name, src)
        return self

    def create_dir(self, name, dest):
        '''Create a directory.'''
        if not osp.isdir(dest):
            os.mkdir(dest)
            print self.MSG_NEWDIR.format(name)
        return self

    def process_dir(self, files, src, dest, relpath):
        '''Process a directory.'''
        prefix = self.args.mako_prefix
        for name in files:
            srcfile = osp.join(src, name)
            destfile = osp.join(dest, name)
            relfile = osp.join(relpath, name)

            if name.startswith(prefix):
                destfile = osp.join(dest, name[len(prefix):])
                self.render_file(relfile, srcfile, destfile)
            else:
                self.copy_file(relfile, srcfile, destfile)s
        return self

    def skip_file(self, name, src, dest):
        '''Skip a file.'''
        print self.MSG_SKIPFILE.format(name, src, dest)
        return self

    def copy_file(self, name, src, dest):
        '''Copy a file.'''
        shutil.copy2(src, dest)
        print self.MSG_COPYFILE.format(name)
        return self

    def render_file(self, name, src, dest):
        '''Render a file.'''
        if (not self.args.ignore_mtime and osp.isfile(dest) and
                osp.getmtime(src) <= osp.getmtime(dest)):  # file isn't newer
            return self.skip_file(name, src, dest)

        tmpl = self._tmpl.get_template(name)
        with codecs.open(dest, encoding='utf-8', mode='w') as out:
            rendered = tmpl.render_unicode(site=self.site, page=Namespace())
            out.write(rendered)
        print self.MSG_RENDERED.format(name)
        return self


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
    Pageit(args, site).run()


if __name__ == '__main__':  # pragma: no cover
    main()
