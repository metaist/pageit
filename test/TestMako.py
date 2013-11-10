#!/usr/bin/python
# coding: utf-8

from os import path as osp
import unittest
import inspect

from nose.plugins.skip import SkipTest, Skip
from mako.lookup import TemplateLookup

CWD = osp.dirname(osp.abspath(inspect.getfile(inspect.currentframe())))


class TestMako(unittest.TestCase):
    def test_run(self):
        """Test Mako Namespace."""
        srcdir = osp.join(CWD, 'example1', 'site')

        tlookup = TemplateLookup(directories=[srcdir])
        tmpl = tlookup.get_template('subdir/mako.index.html')
        self.assertTrue(tmpl is not None)

        output = tmpl.render()
        expected = ('<base>\r\n\r\n<child>\r\n/subdir/index.html\r\n</child>'
                    '\r\n</base>')
        self.assertEquals(expected, output)
