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


"""Test merger corner cases that are unlikely to appear as usage scenarios."""

from __future__ import absolute_import, print_function

from json_merger.comparator import PrimaryKeyComparator


def test_multiple_primary_keys():
    class MyComp(PrimaryKeyComparator):
        primary_key_fields = ['id', 'f.id']

    lst = [{'id': 0}, {'id': 1}, {'f': {'id': 0}}, {'f': {'id': 1}}]
    inst = MyComp(lst, lst)

    for i, obj in enumerate(lst):
        assert inst.get_matches('l1', i) == [(i, obj)]
        assert inst.get_matches('l2', i) == [(i, obj)]


def test_list_of_primary_keys():
    class MyComp(PrimaryKeyComparator):
        primary_key_fields = [['id1', 'id2']]

    lst1 = [{'id1': 0, 'data': 1},
            {'id2': 0, 'data': 1},
            {'id1': 1, 'id2': 1, 'data': 1}]
    lst2 = [{'id1': 0, 'data': 2},
            {'id2': 0, 'data': 2},
            {'id1': 1, 'id2': 1, 'data': 2},
            {'id1': 1, 'id2': 0, 'data': 2}]

    inst = MyComp(lst1, lst2)

    assert not inst.get_matches('l1', 0)
    assert not inst.get_matches('l1', 1)
    assert not inst.get_matches('l2', 0)
    assert not inst.get_matches('l2', 1)
    assert not inst.get_matches('l2', 3)

    assert inst.get_matches('l1', 2) == [(2, lst2[2])]
    assert inst.get_matches('l2', 2) == [(2, lst1[2])]


def test_list_of_primary_keys_normalization():
    class MyComp(PrimaryKeyComparator):
        primary_key_fields = [['id1', 'id2']]
        normalization_functions = {'id2': str.lower}

    lst1 = [{'id1': 0, 'data': 1},
            {'id2': 'a', 'data': 1},
            {'id1': 1, 'id2': 'a', 'data': 1}]
    lst2 = [{'id1': 0, 'data': 2},
            {'id2': 'A', 'data': 2},
            {'id1': 1, 'id2': 'A', 'data': 2},
            {'id1': 1, 'id2': 'B', 'data': 2}]

    inst = MyComp(lst1, lst2)

    assert not inst.get_matches('l1', 0)
    assert not inst.get_matches('l1', 1)
    assert not inst.get_matches('l2', 0)
    assert not inst.get_matches('l2', 1)
    assert not inst.get_matches('l2', 3)

    assert inst.get_matches('l1', 2) == [(2, lst2[2])]
    assert inst.get_matches('l2', 2) == [(2, lst1[2])]
