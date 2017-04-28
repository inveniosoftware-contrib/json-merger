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

from dictdiffer.merge import Merger, UnresolvedConflictsException

from json_merger.config import DictMergerOps
from json_merger.conflict import Conflict, ConflictType
from dictdiffer.conflict import Conflict as Dictdiffer_Conflict
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


# custom ops tests

def test_conflict_with_custom_ops_update():
    r = {'r': {'foo': 'baa', 'spam': 'eg'},
         'p': {'foo': 'baa', 'spam': 'eg'}}
    h = {'r': {'foo': 'bab', 'spam': 'egg'},
         'p': {'foo': 'bab', 'spam': 'egg'}}
    u = {'r': {'foo': 'bac', 'spam': 'eggs'},
         'p': {'foo': 'bac', 'spam': 'eggs'}}

    # set different strategies compare to the default one
    custom_ops = {
        'r': DictMergerOps.FALLBACK_KEEP_UPDATE,
        'p': DictMergerOps.FALLBACK_KEEP_UPDATE
    }
    expected = {
        'r': {'foo': 'bac', 'spam': 'eggs'},
        'p': {'foo': 'bac', 'spam': 'eggs'}
    }

    m = SkipListsMerger(
        r, h, u,
        DictMergerOps.FALLBACK_KEEP_HEAD,
        custom_ops=custom_ops
    )

    with pytest.raises(MergeError) as excinfo:
        m.merge()

    assert m.merged_root == expected
    assert m.conflicts == excinfo.value.content
    assert len(m.conflicts) == 4
    assert Conflict(
        ConflictType.SET_FIELD, ('p', 'foo'), 'bab'
    ) in m.conflicts
    assert Conflict(
        ConflictType.SET_FIELD, ('p', 'foo'), 'bab'
    ) in m.conflicts
    assert Conflict(
        ConflictType.SET_FIELD, ('p', 'foo'), 'bab'
    ) in m.conflicts
    assert Conflict(
        ConflictType.SET_FIELD, ('p', 'foo'), 'bab'
    ) in m.conflicts


def test_conflict_with_custom_ops_update_and_head():
    r = {'r': {'foo': 'baa', 'spam': 'eg'},
         'p': {'foo': 'baa', 'spam': 'eg'}}
    h = {'r': {'foo': 'bab', 'spam': 'egg'},
         'p': {'foo': 'bab', 'spam': 'egg'}}
    u = {'r': {'foo': 'bac', 'spam': 'eggs'},
         'p': {'foo': 'bac', 'spam': 'eggs'}}

    # set custom mixed strategies
    custom_ops = {
        'r': DictMergerOps.FALLBACK_KEEP_UPDATE,
        'p': DictMergerOps.FALLBACK_KEEP_HEAD,
    }
    expected = {
        'r': {'foo': 'bac', 'spam': 'eggs'},
        'p': {'foo': 'bab', 'spam': 'egg'}
    }

    m = SkipListsMerger(
        r, h, u,
        DictMergerOps.FALLBACK_KEEP_HEAD,
        custom_ops=custom_ops
    )
    with pytest.raises(MergeError) as excinfo:
        m.merge()

    assert m.merged_root == expected
    assert m.conflicts == excinfo.value.content
    assert len(m.conflicts) == 4
    assert Conflict(
        ConflictType.SET_FIELD, ('p', 'spam'), 'eggs'
    ) in m.conflicts
    assert Conflict(
        ConflictType.SET_FIELD, ('r', 'spam'), 'egg'
    ) in m.conflicts
    assert Conflict(
        ConflictType.SET_FIELD, ('r', 'foo'), 'bab'
    ) in m.conflicts
    assert Conflict(
        ConflictType.SET_FIELD, ('p', 'foo'), 'bac'
    ) in m.conflicts


def test_conflict_with_custom_ops_update_and_head_mixed():
    r = {'r': {'foo': 'baa', 'spam': 'eg'},
         'p': {'foo': 'baa', 'spam': 'eg'}}
    h = {'r': {'foo': 'bab', 'spam': 'egg'},
         'p': {'foo': 'bab', 'spam': 'egg'}}
    u = {'r': {'foo': 'bac', 'spam': 'eggs'},
         'p': {'foo': 'bac', 'spam': 'eggs'}}

    # set custom mixed strategies with same root
    custom_ops = {
        'r': DictMergerOps.FALLBACK_KEEP_UPDATE,
        'p': DictMergerOps.FALLBACK_KEEP_UPDATE,
        'p.foo': DictMergerOps.FALLBACK_KEEP_HEAD,
    }
    expected = {
        'r': {'foo': 'bac', 'spam': 'eggs'},
        'p': {'foo': 'bab', 'spam': 'eggs'}
    }

    m = SkipListsMerger(
        r, h, u,
        DictMergerOps.FALLBACK_KEEP_HEAD,
        custom_ops=custom_ops
    )
    with pytest.raises(MergeError) as excinfo:
        m.merge()

    assert m.merged_root == expected

    assert m.conflicts == excinfo.value.content
    assert len(m.conflicts) == 4
    assert Conflict(
        ConflictType.SET_FIELD, ('r', 'spam'), 'egg'
    ) in m.conflicts
    assert Conflict(
        ConflictType.SET_FIELD, ('p', 'spam'), 'egg'
    ) in m.conflicts
    assert Conflict(
        ConflictType.SET_FIELD, ('r', 'foo'), 'bab'
    ) in m.conflicts
    assert Conflict(
        ConflictType.SET_FIELD, ('p', 'foo'), 'bac'
    ) in m.conflicts


def test_conflict_with_custom_ops_update_and_head_with_nested_rules():
    r = {'r': {'foo': 'baa', 'spam': 'eg'},
         'p': {'foo': 'baa', 'spam': 'eg'}}
    h = {'r': {'foo': 'bab', 'spam': 'egg'},
         'p': {'foo': 'bab', 'spam': 'egg'}}
    u = {'r': {'foo': 'bac', 'spam': 'eggs'},
         'p': {'foo': 'bac', 'spam': 'eggs'}}

    custom_ops = {
        'r': DictMergerOps.FALLBACK_KEEP_UPDATE,
        'p': DictMergerOps.FALLBACK_KEEP_HEAD,
        'r.foo': DictMergerOps.FALLBACK_KEEP_HEAD,
        'p.spam': DictMergerOps.FALLBACK_KEEP_UPDATE
    }
    expected = {
        'r': {'foo': 'bab', 'spam': 'eggs'},
        'p': {'foo': 'bab', 'spam': 'eggs'}
    }

    m = SkipListsMerger(
        r, h, u,
        DictMergerOps.FALLBACK_KEEP_HEAD,
        custom_ops=custom_ops
    )
    with pytest.raises(MergeError) as excinfo:
        m.merge()

    assert m.merged_root == expected

    assert m.conflicts == excinfo.value.content
    assert len(m.conflicts) == 4
    assert Conflict(
        ConflictType.SET_FIELD, ('r', 'spam'), 'egg'
    ) in m.conflicts
    assert Conflict(
        ConflictType.SET_FIELD, ('p', 'spam'), 'egg'
    ) in m.conflicts
    assert Conflict(
        ConflictType.SET_FIELD, ('r', 'foo'), 'bac'
    ) in m.conflicts
    assert Conflict(
        ConflictType.SET_FIELD, ('p', 'foo'), 'bac'
    ) in m.conflicts


def test_custom_fallback():
    r = {'r': {'foo': 'baa'}}
    h = {'r': {'foo': 'bab'}}
    u = {'r': {'foo': 'bac'}}

    m = SkipListsMerger(r, h, u, DictMergerOps.FALLBACK_KEEP_HEAD)
    with pytest.raises(MergeError) as excinfo:
        m.merge()

    assert m.merged_root == {'r': {'foo': 'bab'}}
    assert m.conflicts == excinfo.value.content
    assert len(m.conflicts) == 1
    assert Conflict(
        ConflictType.SET_FIELD, ('r', 'foo'), 'bac'
    ) in m.conflicts


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


def test_get_custom_strategies():
    patches = [
        Dictdiffer_Conflict(
            ('change', 'p.foo', ('baa', 'bab')),
            ('change', 'p.foo', ('baa', 'bac'))
        ),
        Dictdiffer_Conflict(
            ('change', 'p.spam', ('eg', 'egg')),
            ('change', 'p.spam', ('eg', 'eggs'))
        ),
        Dictdiffer_Conflict(
            ('change', 'r.foo', ('baa', 'bab')),
            ('change', 'r.foo', ('baa', 'bac'))
        ),
        Dictdiffer_Conflict(
            ('change', 'r.spam', ('eg', 'egg')),
            ('change', 'r.spam', ('eg', 'eggs'))
        )
    ]

    custom_ops = {
        'r': DictMergerOps.FALLBACK_KEEP_UPDATE,
        'p': DictMergerOps.FALLBACK_KEEP_UPDATE
    }

    expected_strategies = ['s', 's', 's', 's']

    m = SkipListsMerger(
        {}, {}, {},
        DictMergerOps.FALLBACK_KEEP_HEAD,
        custom_ops=custom_ops
    )

    strategies = m._get_custom_strategies(patches)

    assert expected_strategies == strategies


def test_get_all_the_related_path_perfect_match():
    custom_ops = {
        'a.b.c.d': DictMergerOps.FALLBACK_KEEP_UPDATE
    }

    m = SkipListsMerger(
        {}, {}, {},
        DictMergerOps.FALLBACK_KEEP_HEAD,
        custom_ops=custom_ops
    )

    expected = 's'

    output = m._get_related_path('a.b.c.d')

    assert expected == output


def test_get_all_the_related_path_gerarchy_match():
    custom_ops = {
        'a.b': DictMergerOps.FALLBACK_KEEP_UPDATE
    }

    m = SkipListsMerger(
        {}, {}, {},
        DictMergerOps.FALLBACK_KEEP_HEAD,
        custom_ops=custom_ops
    )

    expected = 's'

    output = m._get_related_path('a.b.c.d')

    assert expected == output


def test_get_all_the_related_path_no_match():
    custom_ops = {
        'a.b': DictMergerOps.FALLBACK_KEEP_UPDATE
    }

    m = SkipListsMerger(
        {}, {}, {},
        DictMergerOps.FALLBACK_KEEP_HEAD,
        custom_ops=custom_ops
    )

    expected = 'f'

    output = m._get_related_path('a.l.c.d')

    assert expected == output
