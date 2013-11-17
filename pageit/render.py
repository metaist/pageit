#!/usr/bin/python
# coding: utf-8

'''pageit generator'''

# Native
from fnmatch import fnmatch
from os import path as osp
import codecs
import logging
import os
import re
import sys

# 3rd Party
from argh import arg, ArghParser
from mako.lookup import TemplateLookup
import mako.exceptions

# Package
if '__main__' == __name__:  # pragma: no cover
    sys.path.insert(0, '.')

try:
    from pageit import tools
    from pageit.namespace import Namespace
    import pageit
except ImportError:  # pragma: no cover
    from . import tools
    from .namespace import Namespace
    import __init__ as pageit  # pylint: disable=W0403

logging.basicConfig(format='%(levelname)-8s %(message)s')

# regex for import line in a mako template
RE_MAKO_IMPORT = re.compile(r'<%(include|inherit|namespace)\s+file="([^"]*)"')

DEFAULT = Namespace(
    log=logging.getLogger('com.metaist.pageit.render'),
    path='.',
    tmp=None,
    ext='.mako',
    port=80,
    verbosity=1
)

MSG_PRE = tools.MSG_PRE
MSG = tools.MSG + Namespace(
    DONE=MSG_PRE + 'done',
    T_RENDER=MSG_PRE + 'started rendering <%s>',
    T_MTIME=MSG_PRE + 'mtime of <%s>',
    T_MTIME_END=MSG_PRE + 'dependencies: %s (%s)',

    DRY=' (dry run)',
    DRY_RUN=MSG_PRE + '** Dry Run! No files will be altered. **',
    IGNORE_MTIME=MSG_PRE + 'Ignoring modification times.',

    NO_CHANGE=MSG_PRE + 'no change in <%s>',
    DELETE=MSG_PRE + 'deleted <%s>',
    DELETE_ERR=MSG_PRE + 'cannot delete %s',
    RENDER=MSG_PRE + 'rendered <%s>',
    RENDER_ERR=MSG_PRE + 'cannot render %s',
    WRITE=MSG_PRE + 'wrote <%s>',
    WRITE_ERR=MSG_PRE + 'cannot write to %s'
)


class Pageit(object):
    '''Mako template renderer.

    Attributes:
        watcher (pageit.tools.Watcher): underlying watcher for this path

    Args:
        path (str, optional): path to traverse; default is current dir

        ext (str, optional): extension to look for

        dry_run (bool, optional): if True, print what would happen instead
            of rendering; default is False

        noerr (bool, optional): if True, don't create error files;
            default is False

        ignore_mtime (bool, optional): if True, do not consider
            template modification times when rendering; default is False.

            Note:
                pageit does not currently warn you if the output is
                *newer* than the template.

        watcher (pageit.tools.Watcher, optional): underlying watcher for the
            given path

            Note:
                You may attach the watcher after this object has been
                constructed via the :py:attr:`~pageit.render.Pageit.watcher`
                attribute.

        tmpl (mako.lookup.TemplateLookup, optioanl): mako template lookup
            object

        log (logging.Logger, optional): system logger
    '''

    _dry = ''
    _outputs = []  # files that are known to be outputs

    # pylint: disable=R0913
    def __init__(self,
                 path=DEFAULT.path,
                 ext=DEFAULT.ext,
                 dry_run=False,
                 noerr=False,
                 ignore_mtime=False,
                 watcher=None,
                 tmpl=None,
                 log=None):
        '''Construct a renderer.'''
        self.path = osp.abspath(path)
        self.watcher = watcher
        self.tmpl = tmpl or create_lookup(self.path)
        self.log = log or create_logger()
        self.args = Namespace(
            ext=ext,
            noerr=noerr,
            dry_run=dry_run,
            ignore_mtime=ignore_mtime
        )

        if dry_run:
            self._dry = MSG.DRY

    def list(self):
        '''Generates list of files to render / clean.

        This function only lists files that end with the appropriate extension,
        will not enter directories that end with that extension.

        Yields:
            str: next file to process
        '''
        pattern = '*' + self.args.ext
        for relpath, _, files in os.walk(self.path):
            src = osp.join(self.path, relpath)
            if fnmatch(src, pattern):  # don't go into this directory
                continue

            for name in files:
                if fnmatch(name, pattern):  # do list this file
                    yield osp.join(src, name)

    def clean(self):
        '''Deletes pageit output files.

        Note:
            This function only deletes files for which there is a corresponding
            template. If the template was moved or deleted, the output will
            not be touched.

        Returns:
            Pageit: for method chaining
        '''
        _context = '[CLEAN]'
        self.log.debug(MSG.START, _context)
        for path in self.list():
            dest = strip_ext(path, self.args.ext)
            if not osp.isfile(dest):  # no output
                continue

            name = osp.relpath(dest, self.path)
            try:
                if not self.args.dry_run:
                    os.remove(dest)
                self.log.info(MSG.DELETE + self._dry, _context, name)
            except OSError:  # pragma: no cover
                self.log.error(MSG.DELTE_ERR, _context, dest)

        self.log.debug(MSG.DONE, _context)
        return self

    def on_change(self, path=None):
        '''React to a change in the directory.

        Args:
            path (str): path that changed

        Returns:
            Pageit: for method chaining
        '''
        if path in self._outputs:
            return self

        return self.run()

    def run(self):
        '''Runs the renderer.

        Returns:
            Pageit: for method chaining
        '''
        _context = '[RENDER]'
        self.log.debug(MSG.START, _context)

        if self.args.dry_run:
            self.log.debug(MSG.DRY_RUN, _context)

        if self.args.ignore_mtime:
            self.log.debug(MSG.IGNORE_MTIME, _context)

        for path in self.list():
            name = osp.relpath(path, self.path)
            dest = strip_ext(path, self.args.ext)

            do_render = True
            if not self.args.ignore_mtime:
                if osp.isfile(dest):  # need to compute modification times
                    output_changed = int(osp.getmtime(dest))
                    template_changed = self.mako_mtime(path)
                    self.log.debug(MSG_PRE + 'output: %s', '[MTIME]',
                                   output_changed)
                    self.log.debug(MSG_PRE + 'template: %s', '[MTIME]',
                                   template_changed)
                    do_render = (template_changed > output_changed)
                    if not do_render:
                        self.log.debug(MSG.NO_CHANGE, _context, name)

            if do_render:
                self.mako(path, dest)

        self.log.debug(MSG.DONE, _context)
        return self

    def mako(self, path, dest=None):
        '''Render a mako template.

        Args:
            path (str): template path
            dest (str, optional): output path; if not provided will be computed

        Returns:
            Pageit: for method chaining
        '''
        _context = '[MAKO]'
        name = osp.relpath(path, self.path)
        self.log.debug(MSG.T_RENDER, _context, name)

        dest = dest or strip_ext(path, self.args.ext)
        tmpl = self.tmpl.get_template(name)
        content, has_errors = '', False
        try:
            if not self.args.dry_run:
                content = tmpl.render_unicode(page=Namespace(path=name))
            self.log.info(MSG.RENDER + self._dry, _context, name)
        except mako.exceptions.MakoException as ex:
            has_errors = True
            self.log.error(MSG.RENDER_ERR, _context, path)
            self.log.error(ex)
            if not self.args.noerr:
                content = mako.exceptions.html_error_template().render()

        if not (self.args.noerr and has_errors):
            try:
                if not self.args.dry_run:
                    with codecs.open(dest, encoding='utf-8', mode='w') as out:
                        out.write(content)
                if dest not in self._outputs:
                    self._outputs.append(dest)
                self.log.debug(MSG.WRITE + self._dry, _context,
                               osp.relpath(dest, self.path))
            except OSError as ex:
                self.log.error(MSG.WRITE_ERR, _context, dest, ex)

        self.log.debug(MSG.DONE, _context)
        return self

    def mako_deps(self, path):
        '''Returns set of immediate dependency paths for a mako template.

        Note:
            This function does not recursively compute dependencies.

        Args:
            path (str): path to a mako template

        Returns:
            set: paths of dependencies
        '''
        paths = set([])
        if not osp.isfile(path):
            return paths

        for line in open(path):
            groups = RE_MAKO_IMPORT.search(line)  # look for imports
            if groups:
                dep = groups.group(2)
                if '/' == dep[0]:  # relative to TemplateLookup.directories
                    dep = osp.normpath(osp.join(self.path, dep.lstrip('/')))
                else:  # relative to template directory
                    dep = osp.normpath(osp.join(osp.dirname(path), dep))

                paths.add(dep)

        return paths

    def mako_mtime(self, path, levels=5):
        '''Returns the modification time of a mako template.

        Note:
            This function considers a limited portion of the template's
            inheritance tree to determine the latest modification time.

        Args:
            path (str): template path
            levels (int): number of inheritance levels to traverse (default: 5)

        Returns:
            int: latest modification time; 0 if the file does not exist

        Examples:
            >>> Pageit().mako_mtime('fake.mako')
            0
        '''
        _context = '[MTIME]'
        name = osp.relpath(path, self.path)
        self.log.debug(MSG.T_MTIME, _context, name)

        if not osp.isfile(path):
            return 0

        deps, next_deps, done, mtimes = set([path]), set([]), [], []
        for _ in range(levels + 1):
            for dep in deps:
                if dep in done or dep in next_deps or not osp.isfile(dep):
                    continue

                next_deps = next_deps.union(self.mako_deps(dep))
                mtimes.append(int(osp.getmtime(dep)))
                done.append(dep)

            if not next_deps:
                break

            deps, next_deps = next_deps, set([])

        self.log.debug(MSG.T_MTIME_END, _context, len(mtimes) - 1,
                       ', '.join([osp.relpath(dep, self.path)
                                  for dep in done[1:]]))
        return max(mtimes)


def create_logger(verbosity=DEFAULT.verbosity, log=None):
    '''Constructs a logger.

    Args:
        verbosity (int): level of verbosity
        log (logging.Logger): an existing logger to modify

    Returns:
        logging.Logger: logger configured based on verbosity.

    Example:
        >>> create_logger() is not None
        True
    '''
    log = log or DEFAULT.log
    if 0 == verbosity:
        log.setLevel(logging.NOTSET)
    elif 1 == verbosity:
        log.setLevel(logging.INFO)
    elif verbosity > 1:
        log.setLevel(logging.DEBUG)
    return log


def create_lookup(path=DEFAULT.path, tmp=None):
    '''Constructs a mako TemplateLookup object.

    Args:
        path (str): top-level path to search for mako templates
        tmp (str, optional): directory to store generated modules

    Returns:
        mako.lookup.TemplateLookup: object to use for searching for templates

    Example:
        >>> create_lookup() is not None
        True
    '''
    return TemplateLookup(
        directories=[path],
        module_directory=tmp,
        input_encoding='utf-8',
        output_encoding='utf-8'
    )


def strip_ext(path, ext):
    '''Remove an extension from a path, if present.

    Args:
        path (str): path from which to strip extension
        ext (str): extension to strip

    Returns:
        str: path with extension removed

    Examples:
        >>> strip_ext('foo.bar', '.bar')
        'foo'
        >>> strip_ext('foo.bar', '.baz')
        'foo.bar'
    '''
    if path.endswith(ext):
        path = path[:-len(ext)]
    return path


@arg('path', nargs='?', default=DEFAULT.path, help='path to process')
@arg('-n', '--dry-run', default=False, help='simulate the process')
@arg('-c', '--clean', default=False, help='remove generated files')
@arg('-r', '--render', default=False,
     help='render templates after --clean')
@arg('-w', '--watch', default=False, help='watch for file modifications')
@arg('-s', '--serve', nargs='?', metavar='PORT', const=DEFAULT.port,
     help='run basic HTTP server; deafult port is ' + str(DEFAULT.port))
@arg('--tmp', metavar='PATH', default=DEFAULT.tmp, help='mako template cache')
@arg('--ignore-mtime', default=False, help='ignore file modification times')
@arg('--noerr', default=False, help='do not generate HTML error output')
@arg('--ext', default=DEFAULT.ext, help='mako file extention')
def render(args):  # pragma: no cover
    '''Convenience method for :py:class:`~pageit.render.Pageit`.

    Args:
        args (Namespace): argh arguments
    '''
    args.path = osp.abspath(args.path)
    log = create_logger(args.verbosity)
    tmpl = create_lookup(args.path, args.tmp)
    runner = Pageit(path=args.path,
                    ext=args.ext,
                    dry_run=args.dry_run,
                    noerr=args.noerr,
                    ignore_mtime=args.ignore_mtime,
                    tmpl=tmpl, log=log)
    if args.clean:
        runner.clean()

    if args.render or args.watch or not args.clean:
        runner.run()  # run at least once

    watch_path = (args.watch and args.path) or None
    with tools.watch(watch_path, runner.on_change, log) as watcher:
        runner.watcher = watcher  # to help pause the watcher during render

        # Wait for CTRL+C either in the server or in a dummy loop.
        if args.serve:
            tools.serve(args.path, args.serve, log)  # server loop
        elif args.watch:
            watcher.loop()  # dummy loop


def main():  # pragma: no cover
    '''Console entry point.

    Constructs and dispatches the argument parser.
    '''
    parser = ArghParser(prog='pageit', description=pageit.__doc__,
                        epilog=pageit.__epilog__)
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + pageit.__version__)
    parser.add_argument('-v', '--verbose', dest='verbosity', action='count',
                        default=1, help='show logging messages')
    parser.add_argument('-q', '--quiet', dest='verbosity',
                        action='store_const', const=0,
                        help='suppress logging messages')
    parser.set_default_command(render)
    parser.dispatch()

if '__main__' == __name__:  # pragma: no cover
    main()
