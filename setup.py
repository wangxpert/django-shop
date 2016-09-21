#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from setuptools import setup, find_packages
import sys
import shop
try:
    from pypandoc import convert
except ImportError:
    def convert(filename, fmt):
        if sys.version_info[0] < 3:
            with open(filename) as fd:
                return fd.read()
        else:
            with open(filename, encoding="utf-8") as fd:
                return fd.read()

CLASSIFIERS = [
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
]

setup(
    author="Jacob Rief",
    author_email="jacob.rief@gmail.com",
    name="django-shop",
    version=shop.__version__,
    description="A RESTful Django Shop",
    long_description=convert('README.md', 'rst'),
    url='http://www.django-shop.org/',
    license='BSD License',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    packages=find_packages(exclude=['example', 'docs', 'testshop']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Django>=1.9',
        'djangocms-cascade>=0.10.0',
        'beautifulsoup4>=4.4.0',
        'django-cms>=3.2.0',
        'django-post-office>=2.0.5',
        'django-filer>=1.2.5',
        'django-ipware>=1.1.1',
        'django-fsm>=2.2.1',
        'djangorestframework>=3.1',
        'django-angular>=0.8.1',
        'django-select2>=5.5.0',
        'django-rest-auth>=0.5.0',
        'django-admin-sortable2>=0.6.3',
    ],
    # Note: this requires setuptools >= 18.0.
    extras_require={
        ':python_version<"3.4"': ['enum34'],
    },
)
