#!/usr/bin/python
# coding: utf-8

# Native
from os import path as osp
import inspect
import os
import unittest

# 3rd Party
from nose.plugins.skip import SkipTest, Skip

# Package
from pageit.render import Pageit
from pageit.namespace import Namespace
import pageit.render as module

CWD = osp.dirname(osp.abspath(inspect.getfile(inspect.currentframe())))


class TestPageit(unittest.TestCase):
    path = osp.join(CWD, 'example1')

    def setUp(self):
        '''Construct the runner.'''
        self.pageit = Pageit(path=self.path)

    def tearDown(self):
        '''Destroy the runner.'''
        self.pageit = None

    def test_create_config(self):
        '''Create site configuration.'''
        infile = osp.join(self.path, 'pageit.yml')

        expected = Namespace(base_url='//localhost/test/example1', debug=True)
        result = module.create_config(infile, 'test')
        self.assertEquals(expected, result)

    def test_mako_deps(self):
        '''List immediate mako dependencies.'''
        infile = osp.join(self.path, 'subdir', 'index.html.mako')

        deps = self.pageit.mako_deps(infile)
        expected = set([osp.join(self.path, 'layouts.mako', 'child.html'),
                        osp.join(self.path, 'subdir', 'local-include.html')])
        self.assertEquals(expected, deps)

    def test_run(self):
        '''Run on a single path.'''
        infile = osp.join(self.path, 'index.html.mako')
        outfile = osp.join(self.path, 'index.html')

        # run
        self.assertFalse(osp.isfile(outfile))
        self.pageit.mako(infile)
        self.assertTrue(osp.isfile(outfile))

        # clean
        self.pageit.clean()
        self.assertFalse(osp.isfile(outfile))

    def test_ignore_subtree(self):
        '''Don't run on directories under a .mako directory (#18).'''
        outfile = osp.join(self.path, 'layouts.mako', 'ignore', 'index.html')
        self.assertFalse(osp.isfile(outfile))
        self.pageit.run()
        self.assertFalse(osp.isfile(outfile))
        self.pageit.clean()

    def test_dry_run(self):
        '''Don't generate files during dry run.'''
        infile = osp.join(self.path, 'index.html.mako')
        outfile = osp.join(self.path, 'index.html')
        self.pageit = Pageit(path=self.path, dry_run=True)

        # run
        self.assertFalse(osp.isfile(outfile))
        self.pageit.mako(infile)
        self.assertFalse(osp.isfile(outfile),
                         'dry run should not generate files')
