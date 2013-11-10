#!/usr/bin/python
# coding: utf-8

from os import path as osp
import unittest
import inspect
import shutil

from nose.plugins.skip import SkipTest, Skip

from pageit import pageit
from pageit.lib import Namespace

CWD = osp.dirname(osp.abspath(inspect.getfile(inspect.currentframe())))


class TestPageit(unittest.TestCase):
    def test_run(self):
        """Basic test."""
        srcdir = osp.join(CWD, 'example1', 'site')
        destdir = osp.join(CWD, 'example1', 'output')
        print destdir
        self.assertFalse(osp.isdir(destdir))

        pageit.main(['--init', '--src', srcdir, '--dest', destdir])
        isdir = osp.isdir(destdir)
        self.assertTrue(isdir)

        if isdir:  # clean up
            shutil.rmtree(destdir)

    def test_mako_deps(self):
        """Listing dependencies in mako."""
        srcdir = osp.join(CWD, 'example1', 'site')
        testfile = osp.join(srcdir, 'subdir', 'mako.index.html')
        obj = pageit.Pageit(args=Namespace(src=srcdir))

        deps = obj.mako_deps(testfile)
        expected = [osp.join(srcdir, 'mako.layouts', 'child.html')]
        self.assertEquals(expected, deps)
