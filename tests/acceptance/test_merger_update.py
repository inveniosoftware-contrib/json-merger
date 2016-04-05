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

from json_merger import merge_with_update


class AuthorComparator(object):

    def distance(self, obj1, obj2):
        return 0 if self.equal(obj1, obj2) else 1

    def equal(self, obj1, obj2):
        if 'inspire_id' in obj1 and 'inspire_id' in obj2:
            return obj1['inspire_id'] == obj2['inspire_id']
        return obj1['full_name'][:5] == obj2['full_name'][:5]


@pytest.mark.xfail
@pytest.mark.parametrize('scenario', [
    'author_typo_update_fix',
    'author_typo_curator_fix',
    'author_typo_update_and_curator_fix',
    'author_typo_conflict',
    'author_prepend_and_curator_typo_fix',
    'author_delete_and_single_curator_typo_fix',
    'author_delete_and_double_curator_typo_fix',
    'author_reorder_and_double_curator_typo_fix',
    'author_reorder_conflict',
    'author_replace_and_single_curator_typo_fix',
    'author_delete_and_double_curator_typo_fix'])
def test_author_typo_scenarios(update_fixture_loader, scenario):
    comparators = {'authors': AuthorComparator()}
    root, head, update, exp, desc = update_fixture_loader.load_test(scenario)
    if exp.get('conflict'):
        merge_with_update(root, head, update, comparators)
    else:
        res = merge_with_update(root, head, update, comparators)
        assert res == exp, desc
