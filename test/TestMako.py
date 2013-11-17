#!/usr/bin/python
# coding: utf-8

# Native
from os import path as osp
import inspect
import unittest

# 3rd Party
from mako.lookup import TemplateLookup
from nose.plugins.skip import SkipTest, Skip

CWD = osp.dirname(osp.abspath(inspect.getfile(inspect.currentframe())))


class TestMako(unittest.TestCase):
    path = osp.join(CWD, 'example1')

    def test_run(self):
        '''Test Mako Namespace.'''
        tlookup = TemplateLookup(directories=[self.path])
        tmpl = tlookup.get_template('subdir/index.html.mako')
        self.assertTrue(tmpl is not None)

        output = tmpl.render()
        print output
        self.assertTrue(output is not None)
        self.assertTrue('' != output)
