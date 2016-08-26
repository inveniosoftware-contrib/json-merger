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

"""Test dictdiffer wrappers."""

from __future__ import absolute_import, print_function

import pytest

from json_merger.config import DictMergerOps
from json_merger.conflict import Conflict, ConflictType
from json_merger.dict_merger import SkipListsMerger
from json_merger.errors import MergeError
from json_merger.nothing import NOTHING


def test_simple_behavior():
    r = {}
    h = {'foo': 'bar'}
    u = {'bar': 'baz'}

    m = SkipListsMerger(r, h, u, DictMergerOps.FALLBACK_KEEP_HEAD)
    m.merge()

    assert m.merged_root == {'foo': 'bar', 'bar': 'baz'}


def test_base_values():
    m = SkipListsMerger(1, 2, 1, DictMergerOps.FALLBACK_KEEP_HEAD)
    m.merge()
    assert m.merged_root == 2

    m = SkipListsMerger(1, 1, 2, DictMergerOps.FALLBACK_KEEP_HEAD)
    m.merge()
    assert m.merged_root == 2


def test_base_values_exceptions():
    m = SkipListsMerger(1, 3, 2, DictMergerOps.FALLBACK_KEEP_HEAD)
    with pytest.raises(MergeError):
        m.merge()
    assert m.conflicts[0] == Conflict(ConflictType.SET_FIELD, (), 2)
    assert m.merged_root == 3

    m = SkipListsMerger(1, 3, 2, DictMergerOps.FALLBACK_KEEP_UPDATE)
    with pytest.raises(MergeError):
        m.merge()
    assert m.conflicts[0] == Conflict(ConflictType.SET_FIELD, (), 3)
    assert m.merged_root == 2


def test_merge_with_nothing():
    m = SkipListsMerger(1, {'some': 'other object'}, NOTHING,
                        DictMergerOps.FALLBACK_KEEP_HEAD)
    m.merge()
    assert m.merged_root == {'some': 'other object'}

    m = SkipListsMerger(1, NOTHING, {'some': 'other object'},
                        DictMergerOps.FALLBACK_KEEP_HEAD)
    m.merge()
    assert m.merged_root == {'some': 'other object'}

    m = SkipListsMerger(NOTHING, {'some': 'other object'}, NOTHING,
                        DictMergerOps.FALLBACK_KEEP_HEAD)
    m.merge()
    assert m.merged_root == {'some': 'other object'}


def test_simple_conflicts_keep_head():
    r = {}
    h = {'foo': 'bar'}
    u = {'foo': 'baz'}

    m = SkipListsMerger(r, h, u, DictMergerOps.FALLBACK_KEEP_HEAD)
    with pytest.raises(MergeError) as excinfo:
        m.merge()

    assert m.merged_root == {'foo': 'bar'}
    assert m.conflicts == excinfo.value.content
    assert len(m.conflicts) == 1
    assert Conflict(ConflictType.SET_FIELD, ('foo', ), 'baz') in m.conflicts


def test_simple_conflicts_keep_update():
    r = {}
    h = {'foo': 'bar'}
    u = {'foo': 'baz'}

    m = SkipListsMerger(r, h, u, DictMergerOps.FALLBACK_KEEP_UPDATE)
    with pytest.raises(MergeError) as excinfo:
        m.merge()

    assert m.merged_root == {'foo': 'baz'}
    assert m.conflicts == excinfo.value.content
    assert len(m.conflicts) == 1
    assert Conflict(ConflictType.SET_FIELD, ('foo', ), 'bar') in m.conflicts


def test_simple_remove_conflict():
    r = {'foo1': 'bar', 'foo2': 'bar'}
    h = {'foo1': 'baz', 'foo2': 'baz'}
    u = {}

    m = SkipListsMerger(r, h, u, DictMergerOps.FALLBACK_KEEP_HEAD)
    with pytest.raises(MergeError) as excinfo:
        m.merge()

    assert m.merged_root == {'foo1': 'baz', 'foo2': 'baz'}
    assert m.conflicts == excinfo.value.content
    assert len(m.conflicts) == 2
    assert Conflict(ConflictType.REMOVE_FIELD, ('foo1', ), None) in m.conflicts
    assert Conflict(ConflictType.REMOVE_FIELD, ('foo2', ), None) in m.conflicts


def test_simple_change_conflict():
    r = {'r': {'foo': 'baa'}}
    h = {'r': {'foo': 'bab'}}
    u = {'r': {'foo': 'bac'}}

    m = SkipListsMerger(r, h, u, DictMergerOps.FALLBACK_KEEP_HEAD)
    with pytest.raises(MergeError) as excinfo:
        m.merge()

    assert m.merged_root == {'r': {'foo': 'bab'}}
    assert m.conflicts == excinfo.value.content
    assert len(m.conflicts) == 1
    assert Conflict(ConflictType.SET_FIELD, ('r', 'foo'), 'bac') in m.conflicts


# Tests for all the list cases.

def test_head_only_list_add_no_skipped_lists():
    r = {'r': {'x': 1}}
    h = {'r': {'x': 1, 'l': [1, 2, 3]}}
    u = {'r': {'x': 2}}

    m = SkipListsMerger(r, h, u, DictMergerOps.FALLBACK_KEEP_HEAD)
    m.merge()

    assert m.merged_root == {'r': {'x': 2, 'l': [1, 2, 3]}}
    assert len(m.skipped_lists) == 0


def test_head_and_update_list_add_skipped_lists():
    r = {'r': {'x': 1}}
    h = {'r': {'x': 1, 'l': [1, 2, 3]}}
    u = {'r': {'x': 2, 'l': [1, 2, 3]}}

    m = SkipListsMerger(r, h, u, DictMergerOps.FALLBACK_KEEP_HEAD)
    m.merge()

    assert m.merged_root == {'r': {'x': 2}}
    # Knowing the list backup method check that m.merge is idempotent.
    assert r == r
    assert h == h
    assert u == u
    assert m.skipped_lists == set([('r', 'l')])


def test_update_deletes_root_list_no_conflict():
    r = {'r': {'x': 1, 'l': [1, 2, 3]}}
    h = {'r': {'x': 1, 'l': [1, 2, 3]}}
    u = {'r': {'x': 2}}

    m = SkipListsMerger(r, h, u, DictMergerOps.FALLBACK_KEEP_HEAD)
    m.merge()

    assert m.merged_root == {'r': {'x': 2}}
    assert len(m.skipped_lists) == 0


def test_one_list_delete_touched_in_head_raises_conflict():
    r = {'r': {'x': 1, 'l': [1, 2, 3]}}
    h = {'r': {'x': 1, 'l': [4, 3, 2, 1]}}
    u = {'r': {'x': 2}}

    m = SkipListsMerger(r, h, u, DictMergerOps.FALLBACK_KEEP_HEAD)
    with pytest.raises(MergeError) as excinfo:
        m.merge()

    assert m.merged_root == {'r': {'x': 2, 'l': [4, 3, 2, 1]}}
    assert len(m.skipped_lists) == 0
    assert m.conflicts == excinfo.value.content
    assert len(m.conflicts) == 1
    assert Conflict(ConflictType.REMOVE_FIELD, ('r', 'l'), None) in m.conflicts


def test_two_list_edit_skipped_lists():
    r = {'r': {'x': 1, 'l1': [1, 2, 3], 'l2': [1]}}
    h = {'r': {'x': 1, 'l1': [4, 3, 2, 1], 'l2': [2]}}
    u = {'r': {'x': 2, 'l1': [1, 2, 3], 'l2': [2]}}

    m = SkipListsMerger(r, h, u, DictMergerOps.FALLBACK_KEEP_HEAD)
    m.merge()

    # The lists are kept as seen in root
    assert m.merged_root == {'r': {'x': 2, 'l1': [1, 2, 3], 'l2': [1]}}
    assert m.skipped_lists == set([('r', 'l1'), ('r', 'l2')])
    # Knowing the list backup method check that m.merge is idempotent.
    assert r == r
    assert h == h
    assert u == u


def test_data_lists_nested():
    r = {'r': [[1, 2, 3], [4, 5, 6]]}
    h = {'r': [[1, 2, 3], [4, 5, 6]]}
    u = {'r': [[3, 3, 3], [4, 5, 6]]}

    m = SkipListsMerger(r, h, u, DictMergerOps.FALLBACK_KEEP_HEAD,
                        data_lists=['r'])
    m.merge()
    assert m.merged_root == u
    assert not m.skipped_lists


def test_data_lists_bare_lists():
    r = [[1, 2, 3], [4, 5, 6]]
    h = [[1, 2, 3], [4, 5, 6]]
    u = [[3, 3, 3], [4, 5, 6]]

    m = SkipListsMerger(r, h, u, DictMergerOps.FALLBACK_KEEP_HEAD)
    m.merge()
    assert m.merged_root == u
    assert not m.skipped_lists
