#!/usr/bin/python
# coding: utf-8

'''pageit: Static site generator.'''

from fnmatch import fnmatch
from os import path as osp
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import TCPServer
import codecs
import logging
import os
import re
import time

from argh import arg, ArghParser
from mako.lookup import TemplateLookup
import mako.exceptions
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from lib import Namespace, pushd  # pylint: disable=W0403
import __init__ as package  # pylint: disable=W0403

logging.basicConfig(format='%(levelname)-8s %(message)s')

RE_MAKO_IMPORT = re.compile(r'<%(include|inherit|namespace)\s+file="([^"]*)"')

DEFAULT = Namespace(
    log=logging.getLogger('com.metaist.pageit'),
    path='.',
    tmp=None,
    ext='.mako',
    port=80,
    verbosity=1
)

MSG_PRE = '%-9s '
MSG = Namespace(
    START=MSG_PRE + 'started ',
    STOP=MSG_PRE + 'stopped',
    DONE=MSG_PRE + 'done',
    T_RENDER=MSG_PRE + 'started rendering <%s>',
    T_SERVE=MSG_PRE + '%s on port [%s]',
    T_WATCH=MSG_PRE + '%s',

    DRY=' (dry run)',
    DRY_RUN=MSG_PRE + '** Dry Run! No files will be altered. **',
    IGNORE_MTIME=MSG_PRE + 'Ignoring modification times.',

    CHANGE=MSG_PRE + 'found change in %s',
    CHANGE_NONE=MSG_PRE + 'no change in <%s>',
    DELETE=MSG_PRE + 'deleted <%s>',
    DELETE_ERR=MSG_PRE + 'cannot delete %s',
    PATH_ERR=MSG_PRE + 'cannot find %s',
    RENDER=MSG_PRE + 'rendered <%s>',
    RENDER_ERR=MSG_PRE + 'cannot render %s',
    WRITE=MSG_PRE + 'wrote <%s>',
    WRITE_ERR=MSG_PRE + 'cannot write to %s'
)


class Pageit(object):
    '''Template renderer.'''

    _mtimes = {}  # template modification times
    _dry = ''

    # pylint: disable=R0913
    def __init__(self, path=DEFAULT.path, ext=DEFAULT.ext,
                 dry_run=False, noerr=False, ignore_mtime=False,
                 tmpl=None, log=None):
        '''Construct a renderer.

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
                    that pageit does not currently warn you if the output is
                    *newer* than the template.
            tmpl (mako.lookup.TemplateLookup, optioanl):
                mako template lookup object
            log (Logging.logger, optional): system logger
        '''

        self.path = osp.abspath(path)
        self.ext = ext
        self.tmpl = tmpl or create_lookup(self.path)
        self.log = log or create_logger()
        self.args = Namespace(
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
        pattern = '*' + self.ext
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
        CONTEXT = '[CLEAN]'  # pylint: disable-msg=C0103
        self.log.debug(MSG.START, CONTEXT)
        for path in self.list():
            dest = strip_ext(path, self.ext)
            if not osp.isfile(dest):  # no output
                continue

            name = osp.relpath(dest, self.path)
            try:
                if not self.args.dry_run:
                    os.remove(dest)
                self.log.info(MSG.DELETE + self._dry, CONTEXT, name)
            except OSError:
                self.log.error(MSG.DELTE_ERR, CONTEXT, dest)

        self.log.debug(MSG.DONE, CONTEXT)
        return self

    def run(self):
        '''Runs the renderer.

        Returns:
            Pageit: for method chaining
        '''
        CONTEXT = '[RENDER]'  # pylint: disable-msg=C0103
        self.log.debug(MSG.START, CONTEXT)

        if self.args.dry_run:
            self.log.debug(MSG.DRY_RUN, CONTEXT)

        if self.args.ignore_mtime:
            self.log.debug(MSG.IGNORE_MTIME, CONTEXT)

        for path in self.list():
            name = osp.relpath(path, self.path)
            dest = strip_ext(path, self.ext)

            do_render = True
            if not self.args.ignore_mtime:
                if osp.isfile(dest):  # need to compute modification times
                    self._mtimes = {}  # reset modification times
                    output_changed = int(osp.getmtime(dest))
                    template_changed = self.mako_mtime(path)
                    do_render = (template_changed > output_changed)
                    if not do_render:
                        self.log.debug(MSG.CHANGE_NONE, CONTEXT, name)

            if do_render:
                self.mako(path, dest)

        self.log.debug(MSG.DONE, CONTEXT)
        return self

    def mako(self, path, dest=None):
        '''Render a mako template.

        Args:
            path (str): template path
            dest (str, optional): output path; if not provided will be computed

        Returns:
            Pageit: for method chaining
        '''
        CONTEXT = '[MAKO]'  # pylint: disable-msg=C0103
        name = osp.relpath(path, self.path)
        if not fnmatch(name, '*' + self.ext):  # some other file was detected
            return

        self.log.debug(MSG.T_RENDER, CONTEXT, name)

        dest = dest or strip_ext(path, self.ext)
        tmpl = self.tmpl.get_template(name)
        content, has_errors = '', False
        try:
            if not self.args.dry_run:
                content = tmpl.render_unicode(page=Namespace(path=name))
            self.log.info(MSG.RENDER + self._dry, CONTEXT, name)
        except mako.exceptions.MakoException as ex:
            has_errors = True
            self.log.error(MSG.RENDER_ERR, CONTEXT, path, ex)
            if not self.args.noerr:
                content = mako.exceptions.html_error_template().render()

        if not (self.args.noerr and has_errors):
            try:
                if not self.args.dry_run:
                    with codecs.open(dest, encoding='utf-8', mode='w') as out:
                        out.write(content)
                self.log.debug(MSG.WRITE + self._dry, CONTEXT,
                               osp.relpath(dest, self.path))
            except OSError as ex:
                self.log.error(MSG.WRITE_ERR, CONTEXT, dest, ex)

        self.log.debug(MSG.DONE, CONTEXT)
        return self

    def mako_deps(self, path):
        '''Returns list of dependency paths for a mako template.

        Args:
            path (str): path to a mako template

        Returns:
            list: paths to dependencies
        '''
        paths = []
        for line in open(path):
            groups = RE_MAKO_IMPORT.search(line)  # look for imports
            if groups:
                dep = groups.group(2)
                if '/' == dep[0]:  # relative to src
                    dep = osp.normpath(osp.join(self.path, dep.lstrip('/')))
                else:  # relative to current dir
                    dep = osp.normpath(osp.join(osp.dirname(path), dep))

                if dep not in paths:
                    paths.append(dep)

        return paths

    def mako_mtime(self, path):
        '''Returns the modification time of a mako template.

        This function considers a template's inheritance tree to determine the
        latest modification time.

        Args:
            path (str): template path

        Returns:
            int: latest modification time
        '''
        if path in self._mtimes:  # in cache
            return self._mtimes[path]

        mtime = max([int(osp.getmtime(path))] +
                    [self.mako_mtime(dep) for dep in self.mako_deps(path)])
        self._mtimes[path] = mtime  # set cache

        return mtime


class Watcher(FileSystemEventHandler):
    '''Handler for file changes.'''

    CONTEXT = '[WATCH]'

    def __init__(self, path=None, callback=None, log=None):
        '''Construct a Watcher to respond to file changes.

        If `path` is not supplied, Watcher will act as a mock object.

        Args:
            path (str): path to watch for changes
            callback (callable): function to run when files change
            log (Logging.logger, optional): logger to use
        '''
        self.path = path
        self.callback = callback
        self.log = log or DEFAULT.log
        self.observer = None

    def __enter__(self):
        '''Run the watch when entering a context.'''
        self.run()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        '''Stop the watch when exiting a context.'''
        self.stop()

    def run(self):
        '''Run the watcher.

        Return immediately if no path had been supplied.
        '''
        if not self.path:  # nothing to do
            return

        self.observer = Observer()
        self.observer.schedule(self, path=self.path, recursive=True)
        self.observer.start()
        self.log.info(MSG.T_WATCH, self.CONTEXT, self.path)

    def loop(self):
        '''Loop until a CTRL+C is pressed.

        If no path is being watched, returns immediately.
        '''
        if not self.path:
            return

        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                print ''  # clear a line in the terminal
                return

    def stop(self):
        '''Stop the watcher.

        Return immediately if no observer had been constructed.
        '''
        if not self.observer:
            return

        self.observer.stop()
        self.observer.join()
        self.log.info(MSG.STOP, self.CONTEXT)

    def on_modified(self, event):
        '''Handle a file modification.

        Args:
            event (object): watchdog event object
        '''
        self.log.info(MSG.CHANGE, self.CONTEXT, event.src_path)
        if self.callback:
            self.callback(event.src_path)


def serve(path, port=DEFAULT.port, log=None):
    '''Serve a path on a given port.

    This function will change the working directory to the path and host it on
    the port specified. If `path` is not supplied, it returns immediately.

    Args:
        path (str): path to host
        port (int, optional): port on which to host; default is 80.
        log (Logging.logger, optional):  logger to use
    '''
    CONTEXT = '[SERVE]'  # pylint: disable-msg=C0103
    assert osp.isdir(path), MSG.PATH_ERR % (CONTEXT, path)

    log = log or DEFAULT.log
    with pushd(path):
        httpd = TCPServer(('', int(port)), SimpleHTTPRequestHandler)
        log.info(MSG.T_SERVE, CONTEXT, path, port)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print  # clear terminal line
            log.info(MSG.STOP, CONTEXT)


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


@arg('--path', default=DEFAULT.path, help='path to process')
@arg('--tmp', metavar='PATH', default=DEFAULT.tmp, help='mako template cache')
@arg('-n', '--dry-run', default=False, help='simulate the process')
@arg('-c', '--clean', default=False, help='remove generated files')
@arg('-w', '--watch', default=False, help='watch for file modifications')
@arg('-s', '--serve', nargs='?', metavar='PORT', const=DEFAULT.port,
     help='run basic HTTP server; deafult port is ' + str(DEFAULT.port))
@arg('--ignore-mtime', default=False, help='ignore file modification times')
@arg('--noerr', default=False, help='do not generate HTML error output')
@arg('--ext', default=DEFAULT.ext, help='mako file extention')
def main(args):  # pragma: no cover
    '''Main entry point.'''
    args.path = osp.abspath(args.path)
    log = create_logger(args.verbosity)
    tmpl = create_lookup(args.path, args.tmp)
    runner = Pageit(path=args.path, ext=args.ext, dry_run=args.dry_run,
                    noerr=args.noerr, ignore_mtime=args.ignore_mtime,
                    tmpl=tmpl, log=log)

    if args.clean:
        runner.clean()

    if not args.clean or args.watch:
        runner.run()  # run at least once

    watch_path = (args.watch and args.path) or None
    with Watcher(watch_path, runner.mako, log) as watcher:
        if args.serve:
            serve(args.path, args.serve, log)
        else:
            watcher.loop()  # wait for CTRL+C


if '__main__' == __name__:  # pragma: no cover
    # pylint: disable=C0103
    epilog = '''Copyright 2013, Metaist.

Licensed under the terms of the MIT license.
Source code at <https://github.com/metaist/pageit>'''

    parser = ArghParser(prog='pageit', description=__doc__, epilog=epilog)
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + package.__version__)
    parser.add_argument('-v', '--verbose', dest='verbosity', action='count',
                        default=1, help='show logging messages')
    parser.add_argument('-q', '--quiet', dest='verbosity',
                        action='store_const', const=0,
                        help='suppress logging messages')

    parser.set_default_command(main)
    parser.dispatch()
