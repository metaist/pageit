#!/usr/bin/python
# coding: utf-8

'''Tools for changing, serving, and watching paths.'''

# Native
from contextlib import contextmanager
from os import path as osp
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import TCPServer
import logging
import os
import time

# 3rd Party
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Package
try:
    from pageit.namespace import Namespace
except ImportError:  # pragma: no cover
    from .namespace import Namespace

DEFAULT = Namespace(
    log=logging.getLogger('com.metaist.pageit.tools'),
    port=80
)

MSG_PRE = '%-9s '
MSG = Namespace(
    START=MSG_PRE + 'started',
    STOP=MSG_PRE + 'stopped',
    T_SERVE=MSG_PRE + '%s on port [%s]',
    T_WATCH=MSG_PRE + '%s',

    CHANGE=MSG_PRE + 'change in %s',
    PATH_ERR=MSG_PRE + 'cannot find %s'
)


@contextmanager
def pushd(path):
    '''Change the current working directory for a context.

    Args:
        path (str): temporary path to change to

    Yields:
        str: absolute path to the new path

    Example:
        >>> cwd = os.getcwd()
        >>> with pushd('..') as newpath:
        ...     os.getcwd() != cwd
        True
    '''
    oldpath, newpath = os.getcwd(), os.path.abspath(path)
    os.chdir(newpath)
    yield newpath
    os.chdir(oldpath)


def serve(path, port=DEFAULT.port, log=None):  # pragma: no cover
    '''Serve a path on a given port.

    This function will change the working directory to the path and host it on
    the port specified. If `path` is not supplied, it returns immediately.

    Args:
        path (str): path to host
        port (int, optional): port on which to host; default is 80.
        log (logging.Logger, optional):  logger to use
    '''
    _context = '[SERVE]'
    assert osp.isdir(path), MSG.PATH_ERR % (_context, path)

    log = log or DEFAULT.log
    with pushd(path):
        httpd = TCPServer(('', int(port)), SimpleHTTPRequestHandler)
        log.info(MSG.T_SERVE, _context, path, port)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print  # clear terminal line
            log.info(MSG.STOP, _context)


@contextmanager
def watch(path=None, callback=None, log=None):  # pragma: no cover
    '''Watch a directory and call the given callback when it changes.

    This is a convenience method for :py:class:`~pageit.tools.Watcher`.

    Args:
        path (str): path to watch
        callback (callable): callable to call when path changes; will be passed
            the path to the file that changed
        log (logging.Logger, optional): logger to use

    Yields:
        Watcher: file system event handler for this watch
    '''
    log = log or DEFAULT.log
    watcher = Watcher(path=path, callback=callback, log=log)
    if not path:
        yield watcher
        return

    watcher.start()
    yield watcher
    watcher.stop()


class Watcher(FileSystemEventHandler):
    '''Handler for file changes.

    Args:
        path (str): path to watch
        callback (callable): function to run when files change
        log (logging.Logger, optional): logger to use
    '''

    _context = '[WATCH]'
    _watch = None
    _paused = False

    def __init__(self, path=None, callback=None, log=None):
        '''Construct a Watcher to respond to file changes.'''
        self.path = path
        self.callback = callback
        self.observer = None
        self.log = log or DEFAULT.log

    def __enter__(self):
        '''Enter a context.

        Returns:
            Watcher: this watcher
        '''
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        '''Exit a context.'''
        self.stop()

    def on_modified(self, event=None):
        '''Handle a file modification.

        Args:
            event (object): watchdog event object

        Returns:
            Watcher: for method chaining
        '''
        if self.callback and not self._paused:
            path = (event and event.src_path) or None
            self.log.info(MSG.CHANGE, self._context, path)
            self.callback(path)
        return self

    def start(self):
        '''Start the underlying observer.

        Returns:
            Watcher: for method chaining
        '''
        if self.observer:  # already started
            return self

        self.observer = Observer()
        if self.path:
            self._watch = self.observer.schedule(self, path=self.path,
                                                 recursive=True)
        self.observer.start()
        self.log.info(MSG.T_WATCH, self._context, self.path)

        return self

    def stop(self):
        '''Stop the underlying observer.

        Returns:
            Watcher: for method chaining
        '''
        if not self.observer:  # already stopped
            return self

        self.observer.stop()
        self.observer.join()
        self.observer = None
        self.log.info(MSG.STOP, self._context)

        return self

    def loop(self):
        '''Run until CTRL+C is pressed.

        Returns:
            Watcher: for method chaining
        '''
        if not self.observer or not self.path:  # nothing to wait for
            return self

        while True:  # pragma: no cover
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                print ''  # clear a line in the terminal
                return self
