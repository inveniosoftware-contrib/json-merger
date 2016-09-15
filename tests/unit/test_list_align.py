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


"""Test list aligner correct output."""

from __future__ import absolute_import, print_function

import pytest

from json_merger.config import UnifierOps
from json_merger.conflict import ConflictType
from json_merger.comparator import PrimaryKeyComparator
from json_merger.errors import MergeError
from json_merger.list_unify import ListUnifier
from json_merger.nothing import NOTHING


def test_value_error():
    with pytest.raises(ValueError):
        ListUnifier([], [], [], 'BAD_OPERATION')


def test_keep_only_head_entitites():
    root = [1, 2]
    head = [1, 2, 3]
    update = [6, 5, 4, 3, 2]

    u = ListUnifier(root, head, update, UnifierOps.KEEP_ONLY_HEAD_ENTITIES)
    u.unify()

    assert u.unified == [(1, 1, NOTHING), (2, 2, 2), (NOTHING, 3, 3)]


def test_keep_only_update_entities():
    root = [1, 2]
    head = [6, 5, 4, 3, 2]
    update = [1, 2, 3]

    u = ListUnifier(root, head, update, UnifierOps.KEEP_ONLY_UPDATE_ENTITIES)
    u.unify()

    assert u.unified == [(1, NOTHING, 1), (2, 2, 2), (NOTHING, 3, 3)]


def test_keep_update_and_head_ent_head_fst():
    root = [1, 2]
    head = [5, 4, 3, 2]
    update = [10, 3, 1, 2, 11]

    u = ListUnifier(root, head, update,
                    UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST)
    u.unify()

    assert u.unified == [(NOTHING, 5, NOTHING), (NOTHING, 4, NOTHING),
                         (NOTHING, NOTHING, 10),
                         (NOTHING, 3, 3), (1, NOTHING, 1),
                         (2, 2, 2),
                         (NOTHING, NOTHING, 11)]


def test_keep_update_and_head_ent_update_fst():
    root = [1, 2]
    head = [5, 4, 3, 2]
    update = [10, 3, 1, 2, 11]

    u = ListUnifier(root, head, update,
                    UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_UPDATE_FIRST)
    u.unify()

    assert u.unified == [(NOTHING, NOTHING, 10),
                         (NOTHING, 5, NOTHING), (NOTHING, 4, NOTHING),
                         (NOTHING, 3, 3), (1, NOTHING, 1),
                         (2, 2, 2),
                         (NOTHING, NOTHING, 11)]


def test_keep_update_and_head_ent_head_fst_fallback():
    root = [1, 2]
    head = [1, 2, 3]
    update = [7, 3, 6, 1, 5, 2, 4]

    u = ListUnifier(root, head, update,
                    UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST)

    with pytest.raises(MergeError) as excinfo:
        u.unify()

    assert len(excinfo.value.content) == 1
    conflict = excinfo.value.content[0]
    assert conflict.conflict_type == ConflictType.REORDER
    assert conflict.path == ()
    assert conflict.body is None

    assert u.unified == [(1, 1, 1), (2, 2, 2), (NOTHING, 3, 3),
                         (NOTHING, NOTHING, 7),
                         (NOTHING, NOTHING, 6),
                         (NOTHING, NOTHING, 5),
                         (NOTHING, NOTHING, 4)]


def test_error_on_head_delete():
    root = [1, 2]
    head = [1, 2, 3, 5]
    update = [1, 2, 4]

    u = ListUnifier(root, head, update,
                    UnifierOps.KEEP_UPDATE_ENTITIES_CONFLICT_ON_HEAD_DELETE)

    with pytest.raises(MergeError) as excinfo:
        u.unify()
    assert len(excinfo.value.content) == 2

    expect_removed = {3, 5}
    removed = set()
    for conflict in excinfo.value.content:
        assert conflict.conflict_type == ConflictType.ADD_BACK_TO_HEAD
        assert conflict.path == ()
        removed.add(conflict.body)
    assert removed == expect_removed

    assert u.unified == [(1, 1, 1), (2, 2, 2), (NOTHING, NOTHING, 4)]


def test_no_error_on_head_delete_from_root():
    root = [1, 2]
    head = [1, 2]
    update = [1, 4]

    u = ListUnifier(root, head, update,
                    UnifierOps.KEEP_UPDATE_ENTITIES_CONFLICT_ON_HEAD_DELETE)
    u.unify()
    assert u.unified == [(1, 1, 1), (NOTHING, NOTHING, 4)]


def test_error_on_multiple_match():
    root = [2, 3]
    head = [1, 1, 2, 3, 3]
    update = [1, 2, 3]

    u = ListUnifier(root, head, update,
                    UnifierOps.KEEP_ONLY_UPDATE_ENTITIES)
    with pytest.raises(MergeError) as excinfo:
        u.unify()

    assert len(excinfo.value.content) == 4
    expected_bodies = [(None, 1, 1), (None, 1, 1), (3, 3, 3), (3, 3, 3)]
    for conflict in excinfo.value.content:
        assert conflict.conflict_type == ConflictType.MANUAL_MERGE
        assert conflict.path == ()
        assert conflict.body in expected_bodies
        expected_bodies.remove(conflict.body)
    assert not expected_bodies

    assert u.unified == [(2, 2, 2)]


def test_multiple_match_symmetry():
    root = []
    l1 = [1, 2, 3, 3, 3]
    l2 = [1, 2, 3]

    u1 = ListUnifier(root, l1, l2,
                     UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST)
    u2 = ListUnifier(root, l2, l1,
                     UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_UPDATE_FIRST)

    with pytest.raises(MergeError) as u1_excinfo:
        u1.unify()
    with pytest.raises(MergeError) as u2_excinfo:
        u2.unify()

    assert len(u1_excinfo.value.content) == 3
    assert len(u2_excinfo.value.content) == 3

    for conflict in u1_excinfo.value.content + u2_excinfo.value.content:
        assert conflict.conflict_type == ConflictType.MANUAL_MERGE
        assert conflict.path == ()
        assert conflict.body == (None, 3, 3)

    assert u1.unified == [(NOTHING, 1, 1), (NOTHING, 2, 2)]
    assert u2.unified == [(NOTHING, 1, 1), (NOTHING, 2, 2)]


def test_stats():
    root = [1, 2, 10]
    head = [1, 3, 4, 2]
    update = [1, 3, 5]

    u = ListUnifier(root, head, update,
                    UnifierOps.KEEP_ONLY_UPDATE_ENTITIES)
    u.unify()

    assert sorted(u.head_stats.in_result) == [1, 3]
    assert sorted(u.head_stats.not_in_result) == [2, 4]
    assert sorted(u.head_stats.not_in_result_root_match) == [2]
    assert sorted(u.head_stats.not_in_result_root_match_idx) == [3]
    assert sorted(u.head_stats.not_in_result_not_root_match) == [4]
    assert sorted(u.head_stats.not_in_result_root_match_pairs) == [(2, 2)]
    assert sorted(u.head_stats.not_matched_root_objects) == [10]

    assert sorted(u.update_stats.in_result) == [1, 3, 5]
    assert sorted(u.update_stats.not_in_result) == []
    assert sorted(u.update_stats.not_in_result_root_match) == []
    assert sorted(u.update_stats.not_in_result_not_root_match) == []
    assert sorted(u.update_stats.not_matched_root_objects) == [2, 10]


def test_transitive_equality():
    class Comp(PrimaryKeyComparator):
        primary_key_fields = ['id0', 'id1']

    only0 = {'id0': 0}
    only1 = {'id1': 1}
    both = {'id0': 0, 'id1': 1}

    u = ListUnifier([only0], [both], [only1],
                    UnifierOps.KEEP_ONLY_UPDATE_ENTITIES, Comp)
    u.unify()
    assert u.unified == [(only0, both, only1)]

    u = ListUnifier([only0], [only1], [both],
                    UnifierOps.KEEP_ONLY_HEAD_ENTITIES, Comp)
    u.unify()
    assert u.unified == [(only0, only1, both)]

    u = ListUnifier([only0], [only1], [both],
                    UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST, Comp)
    u.unify()
    assert u.unified == [(only0, only1, both)]
