#!/usr/bin/python
# coding: utf-8

from os import path as osp
import inspect
import os
import unittest

from nose.plugins.skip import SkipTest, Skip

from pageit import pageit
from pageit.lib import Namespace

CWD = osp.dirname(osp.abspath(inspect.getfile(inspect.currentframe())))


class TestPageit(unittest.TestCase):
    path = osp.join(CWD, 'example1')

    def setUp(self):
        '''Construct the runner.'''
        self.pageit = pageit.Pageit(path=self.path)

    def tearDown(self):
        '''Destroy the runner.'''
        self.pageit = None

    def test_mako_deps(self):
        '''List mako dependencies.'''
        infile = osp.join(self.path, 'subdir', 'index.html.mako')

        deps = self.pageit.mako_deps(infile)
        expected = [osp.join(self.path, 'layouts.mako', 'child.html'),
                    osp.join(self.path, 'layouts.mako', 'base.html'),
                    osp.join(self.path, 'subdir', 'local-include.html')]
        self.assertEquals(expected, deps)

    def test_run(self):
        '''Run on a single path.'''
        infile = osp.join(self.path, 'index.html.mako')
        outfile = osp.join(self.path, 'index.html')

        # run
        self.assertFalse(osp.isfile(outfile))
        print self.pageit.path
        self.pageit.mako(infile)
        self.assertTrue(osp.isfile(outfile))

        # clean
        self.pageit.clean()
        self.assertFalse(osp.isfile(outfile))

    def test_dry_run(self):
        '''Don't generate files during dry run.'''
        infile = osp.join(self.path, 'index.html.mako')
        outfile = osp.join(self.path, 'index.html')
        self.pageit = pageit.Pageit(path=self.path, dry_run=True)

        # run
        self.assertFalse(osp.isfile(outfile))
        self.pageit.mako(infile)
        self.assertFalse(osp.isfile(outfile),
                         'dry run should not generate files')
