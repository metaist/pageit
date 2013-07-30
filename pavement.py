#!/usr/bin/python
# coding: utf-8

'''Paver build file.'''

from glob import glob
import os
import shutil

from paver.easy import *
from paver.setuputils import setup


setup(
    name='pageit',
    scripts=['pageit.py'],
    version='0.0.1',
    url="http://metaist.com/",
    author="The Metaist",
    author_email="metaist@metaist.com"
)


@task
@needs(['resolve', 'clean', 'test'])
def all():
    pass


@task
def resolve():
    import pip
    pip.main(['install', '-r', 'requirements.txt', '--use-mirrors'])


@task
def clean():
    paths = (glob('.coverage') + glob('MANIFEST') +
             glob('dist/') + glob('build/'))
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
    import nose
    path = os.path.join(os.path.abspath('.'), 'pageit')
    args = ['', '--with-doctest', '--with-coverage', '--cover-package=pageit']
    args += glob(os.path.join(path, '*.py'))
    nose.run(argv=args)


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
