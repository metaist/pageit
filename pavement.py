#!/usr/bin/python
# coding: utf-8

'''Paver build file.'''

import sys
from glob import glob
import os
import shutil

from paver.easy import *
from paver.setuputils import setup

sys.path.insert(0, '')
from pageit import pageit
from pageit.lib import Namespace

IS_WINDOWS = sys.platform.startswith('win')


def check_scripts(scripts):
    '''Add Windows scripts when needed.'''
    if IS_WINDOWS:
        scripts += [script + '.bat' for script in scripts]
    return scripts


OPTS = Namespace(
    name='pageit',
    packages=['pageit'],
    install_requires=['Mako', 'Markdown', 'PyYAML', 'watchdog'],
    scripts=check_scripts(['scripts/pageit']),
    entry_points={'console_scripts': ['pageit = pageit.pageit:main']},
    version=pageit.__version__.replace('pre', ''),
    author=pageit.__author__,
    author_email=pageit.__email__,
    url='https://github.com/metaist/pageit',
    download_url='https://github.com/metaist/pageit',
    description=pageit.__doc__.split('\n')[0],
    long_description=pageit.__doc__,
    keywords='static website',
    license=pageit.__license__,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries'
    ]
)

setup(**OPTS)


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
             glob('dist/') + glob('build/') + glob('pageit.egg-info/'))
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


@task
@needs(['register', 'sdist', 'upload'])
def pypi():
    pass
