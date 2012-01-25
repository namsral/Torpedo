#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Schedule HTTP Callbacks at a defined time in the future.',
    'license': 'MIT',
    'author': 'Lars Wiegman',
    'url': 'http://github.com/namsral/torpedo',
    'author_email': 'lars+torpedo@namsral.com',
    'version': '0.1',
    'install_requires': ['tornado>=2.0'],
    'packages': ['torpedo'],
    'name': 'torpedo',
    'entry_points': {
        'console_scripts': [
            'torpedo = torpedo.app:main',
            ],
        },
}

setup(**config)
