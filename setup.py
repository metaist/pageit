#!/usr/bin/python
# coding: utf-8

'''pageit setup file.'''
from setuptools import setup
import os.path
import sys

sys.path.insert(0, '')
import pageit
from pageit.lib import Namespace
from pageit import pageit as module


def check_scripts(scripts):
    '''Add Windows scripts when needed.'''
    if sys.platform.startswith('win'):
        scripts += [script + '.bat' for script in scripts]
    return scripts


OPTS = Namespace(
    name='pageit',
    description=module.__doc__.split('\n')[0],
    long_description=module.__doc__,

    version=pageit.__version__.replace('pre', ''),
    packages=['pageit'],
    provides=['pageit'],

    install_requires=open('requirements.txt').read().strip().split('\n'),
    scripts=check_scripts(['scripts/pageit']),
    entry_points={'console_scripts': ['pageit = pageit.pageit:main']},

    author=pageit.__author__,
    author_email=pageit.__email__,
    license=pageit.__license__,

    url='https://github.com/metaist/pageit',
    download_url='https://github.com/metaist/pageit',

    keywords='static website generator',
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

if sys.version_info >= (3,):
    OPTS['use_2to3'] = True

setup(**OPTS)
