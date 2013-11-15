#!/usr/bin/python
# coding: utf-8

'''Paver build file.'''

import sys
from glob import glob
import os
import shutil

from paver.easy import *
from paver.setuputils import setup


# Bring in setup.py
exec(''.join([x for x in path('setup.py').lines() if 'setuptools' not in x]))


@task
@needs(['clean', 'test', 'docs'])
def all():
    pass


@task
def resolve():
    import pip
    pip.main(['install', '-r', 'requirements.txt', '--use-mirrors'])


@task
def api_docs():
    args = ['sphinx-apidoc', '-f', '-o', path('docs') / 'api', 'pageit']
    sh(' '.join(args))


@task
@needs(['build_sphinx'])
def docs():
    build = path('build')
    html = build / 'sphinx' / 'html'
    tmp = build / 'html'
    docs = build / 'docs'

    shutil.move(html, build)

    if os.path.isdir(docs):
        shutil.rmtree(docs)

    os.rename(tmp, docs)


@task
def clean():
    paths = (glob('dist/') + glob('build/') + glob('tmp/') +
             glob('pageit.egg-info/') + glob('MANIFEST') + glob('.coverage'))

    for pattern in ['*.pyc', '*.*~']:
        paths += glob(pattern) + glob('*/' + pattern)

    count = len(paths)
    if count > 0:
        print 'Paths to clean:', count

    for path in paths:
        print path
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)
        else:
            print 'Unknown type of path:', path


@task
@needs(['_pep8', '_pylint', '_nose'])
def test():
    pass


@task
def _nose():
    args = ['nosetests', '--all-modules', '--traverse-namespace',
            '--with-doctest', '--with-coverage', '--cover-package=pageit']
    sh(' '.join(args))


@task
def _pep8():
    import pep8
    paths = glob('*.py') + glob('*/*.py')
    pep8style = pep8.StyleGuide()
    pep8style.check_files(paths)


@task
def _pylint():
    from pylint import lint
    args = ['pageit', '--rcfile=.pylint.ini']
    lint.Run(args, exit=False)


@task
@needs(['sdist', 'upload'])
def pypi():
    pass


@task
@needs(['docs', 'upload_docs'])
def pypi_docs():
    pass
