#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import mithril

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

required = [
    'django',
    'netaddr==0.7.6',
]
packages = [
    'mithril',
    'mithril.tests',
]

setup(
    name='django-mithril',
    version='%d.%d.%d' % mithril.__version__,
    description='IP Whitelisting for Django',
    long_description=open('README.md').read(),
    author='Chris Dickinson',
    author_email='chris@neversaw.us',
    url='http://urbanairship.github.com/django-mithril/',
    packages=packages,
    package_data={'': ['LICENSE']},
    include_package_data=True,
    install_requires=required,
    license=open("LICENSE").read(),
    zip_safe=False,
    classifiers=(
        'Development Status :: 1 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ),
)
