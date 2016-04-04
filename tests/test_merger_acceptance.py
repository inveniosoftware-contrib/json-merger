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


"""Acceptance scenarios for the merger."""

from __future__ import absolute_import, print_function

import pytest

from json_merger import Merger


@pytest.fixture
def author_distance():
    def distance(a1, a2):
        if a1 == a2:
            return 0

        if not isinstance(a1, dict):
            return 1
        if not isinstance(a2, dict):
            return 1

        if 'full_name' not in a1:
            return 1
        if 'full_name' not in a2:
            return 1

        if a1['full_name'][:5] == a2['full_name'][:5]:
            return 0

        return 1

    return distance


@pytest.mark.parametrize('scenario', [
    'author_list_basic/author_typo',
    'author_list_basic/author_prepend',
    'author_list_basic/author_delete',
    'author_list_basic/author_prepend_and_typo',
    'author_list_basic/author_delete_and_typo'])
def test_expected_outcome_authors(json_loader, author_distance, scenario):
    m = Merger({'ALLOW_REMOVES_FROM': ['authors']}, author_distance)
    src, update, expected, desc = json_loader.load_test(scenario)

    merged = m.merge_records(src, update)
    assert merged == expected, desc
