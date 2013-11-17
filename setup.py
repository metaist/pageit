#!/usr/bin/python
# coding: utf-8

'''pageit setup file.'''

# Native
from setuptools import setup
import sys

# Package
sys.path[0:0] = ['.']
import pageit


def check_scripts(scripts):
    '''Add Windows scripts when needed.'''
    if sys.platform.startswith('win'):
        scripts += [script + '.bat' for script in scripts]
    return scripts


def get_deps(path):
    '''Parse requirements file.'''
    deps = []
    for line in open(path):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        deps.append(line)
    return deps

    open('requirements.txt').read().strip().split('\n')

OPTS = {
    'name': 'pageit',
    'description': pageit.__doc__.split('\n')[0],
    'long_description': pageit.__doc__,

    'version': pageit.__version__.replace('pre', ''),
    'packages': ['pageit', 'test'],
    'provides': ['pageit'],

    'install_requires': get_deps('requirements.txt'),
    'scripts': check_scripts(['scripts/pageit']),
    'entry_points': {'console_scripts': ['pageit = pageit.render:main']},

    'author': pageit.__author__,
    'author_email': pageit.__email__,
    'license': pageit.__license__,

    'url': 'https://github.com/metaist/pageit',
    'download_url': 'https://github.com/metaist/pageit',

    'keywords': 'static website generator',
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries',
    ]
}

if sys.version_info >= (3,):
    OPTS['use_2to3'] = True

setup(**OPTS)
