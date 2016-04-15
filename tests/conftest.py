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


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import json
import os

import pytest


class AbstractFixtureLoader(object):
    def __init__(self, basedir):
        self.basedir = basedir

    def _read_file(self, test_dir, file_name):
        with open(os.path.join(self.basedir, test_dir, file_name)) as f:
            return f.read()

    def load_single(self, test_dir, file_name):
        return json.loads(self._read_file(test_dir, file_name))

    def load_test(self, test_dir):
        raise NotImplementedError('You have to implement me!')


@pytest.fixture()
def update_fixture_loader():
    class _Loader(AbstractFixtureLoader):

        def load_test(self, test_dir):
            root = self.load_single(test_dir, 'root.json')
            head = self.load_single(test_dir, 'head.json')
            update = self.load_single(test_dir, 'update.json')
            expected = self.load_single(test_dir, 'expected.json')
            desc = self._read_file(test_dir, 'description.txt')
            return root, head, update, expected, desc

    return _Loader('./tests/fixtures/update_scenarios/')
