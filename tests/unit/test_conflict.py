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

import json

from json_merger.conflict import Conflict


def test_to_json_with_reorder():
    conflict = Conflict('REORDER', ('foo', 'bar'), {})
    conflict_json = conflict.to_json()
    assert json.loads(conflict_json) == [
        {
            '$type': 'REORDER',
            'op': 'replace',
            'path': '/foo/bar',
            'value': {}
        }
    ]


def test_to_json_with_set_field():
    conflict = Conflict('SET_FIELD', ('foo', 'bar'), {})
    conflict_json = conflict.to_json()
    assert json.loads(conflict_json) == [
        {
            '$type': 'SET_FIELD',
            'op': 'replace',
            'path': '/foo/bar',
            'value': {}
        }
    ]


def test_to_json_with_manual_merge():
    body = [
        None,
        {'foo1': 'bar1'},
        {'foo2': 'bar2'}
    ]
    conflict = Conflict('MANUAL_MERGE', ('foo', 'bar'), body)
    conflict_json = conflict.to_json()
    assert json.loads(conflict_json) == [
        {
            '$type': 'MANUAL_MERGE',
            'op': 'add',
            'path': '/foo/bar/-',
            'value': {'foo1': 'bar1'}
        },
        {
            '$type': 'MANUAL_MERGE',
            'op': 'add',
            'path': '/foo/bar/-',
            'value': {'foo2': 'bar2'}
        }
    ]


def test_to_json_with_add_back_to_head():
    conflict = Conflict('ADD_BACK_TO_HEAD', ('foo', 'bar'), {})
    conflict_json = conflict.to_json()
    assert json.loads(conflict_json) == [
        {
            '$type': 'ADD_BACK_TO_HEAD',
            'op': 'add',
            'path': '/foo/bar/-',
            'value': {}
        }
    ]


def test_to_json_with_remove_field():
    conflict = Conflict('REMOVE_FIELD', ('foo', 'bar'), None)
    conflict_json = conflict.to_json()
    assert json.loads(conflict_json) == [
        {
            '$type': 'REMOVE_FIELD',
            'op': 'remove',
            'path': '/foo/bar',
            'value': None
        }
    ]


def test_to_json_when_path_has_integers():
    conflict = Conflict('REMOVE_FIELD', ('foo', 0, 'bar', 1), None)
    conflict_json = conflict.to_json()
    assert json.loads(conflict_json) == [
        {
            '$type': 'REMOVE_FIELD',
            'op': 'remove',
            'path': '/foo/0/bar/1',
            'value': None
        }
    ]
