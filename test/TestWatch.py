#!/usr/bin/python
# coding: utf-8

# Native
from os import path as osp
import inspect
import os
import unittest
import time

# 3rd Party
from nose.plugins.skip import SkipTest, Skip
from watchdog.observers import Observer

# Package
from pageit import tools
from pageit.namespace import Namespace

CWD = osp.dirname(osp.abspath(inspect.getfile(inspect.currentframe())))


class TestWatch(unittest.TestCase):
    path = osp.join(CWD, 'example1')

    def test_mock_watch(self):
        '''Test a mock watcher.'''
        expected = 'EXPECTED RESULT'

        def handler(path):
            self.assertTrue(expected, path)

        with tools.Watcher(callback=handler) as watcher:
            watcher.start().loop()
            watcher.on_modified(Namespace(src_path=expected)).stop()

    def test_real_watch(self):
        '''Watch a directory for changes.'''
        self.count = 0
        expected = osp.join(self.path, 'subdir', 'index.html.mako')

        def handler(path):
            self.assertTrue(expected, path)
            self.count += 1

        with tools.watch(self.path, handler) as watcher:
            self.assertEquals(0, self.count)

            # Initial
            os.utime(expected, None)
            time.sleep(0.5)
            self.assertEquals(1, self.count, 'should handle file change')

            # Stop
            watcher.stop()
            os.utime(expected, None)
            time.sleep(0.5)
            self.assertEquals(1, self.count,
                              'should not fire when observer is off')

            # Restart
            watcher.start()
            os.utime(expected, None)
            time.sleep(0.5)
            self.assertEquals(2, self.count,
                              'should fire when observer is back on')
