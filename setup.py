# -*- coding: utf-8 -*-
#
# This file is part of Inspirehep.
# Copyright (C) 2016 CERN.
#
# Inspirehep is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Inspirehep is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Inspirehep; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Python module that is able to merge json record objects."""

import sys

from setuptools import find_packages, setup

readme = open('README.rst').read()
version_info = sys.version_info[:2] 

tests_require = [
    'coverage>=4.0',
    'isort>=4.2.2',
    'pydocstyle>=1.0.0',
    'pytest-cache>=1.0',
    'pytest-cov>=1.8.0',
    'pytest>=4.6.11',
    'flake8>=3.9.0',
]

contrib_require = [
    'editdistance>=0.3.1',
    'munkres<=1.0.12',
    'Unidecode==0.4.19' if version_info <= (2, 7) else 'Unidecode>=0.4.19'
]

tests_require += contrib_require

extras_require = {
    'contrib': contrib_require,
    'tests': tests_require
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

install_requires = [
    'bump2version~=0.0,<1' if version_info <= (2, 7) else 'bump2version~=1.0',
    'dictdiffer==0.8.1' if version_info <= (2, 7) else 'dictdiffer>=0.6.0',
    'six>=1.10.0',
    'pyrsistent>=0.11.13'
]

packages = find_packages()

setup(
    name='json-merger',
    description=__doc__,
    long_description=readme,
    keywords='JSON patch merge conflict',
    license='GPLv2',
    author='CERN',
    author_email='admin@inspirehep.net',
    url='https://github.com/inveniosoftware-contrib/json-merger',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
    },
    version='0.7.13',
    extras_require=extras_require,
    install_requires=install_requires,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Development Status :: 4 - Beta',
    ],
)
