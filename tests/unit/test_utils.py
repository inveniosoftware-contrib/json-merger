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

"""Test utils."""

from __future__ import absolute_import, print_function

import pytest

from json_merger.utils import (
    del_obj_at_key_path, get_obj_at_key_path, set_obj_at_key_path,
    get_conf_set_for_key_path, remove_prefix, force_list)


def test_del_obj_at_key_path():
    o = {'a': [{'a': [1, 2, 3]}]}
    del_obj_at_key_path(o, ['a', 0, 'a', 1])
    assert o == {'a': [{'a': [1, 3]}]}

    del_obj_at_key_path(o, ['a', 0, 5], False)
    assert o == {'a': [{'a': [1, 3]}]}

    with pytest.raises(KeyError):
        del_obj_at_key_path(o, ['a', 0, 5])
    with pytest.raises(KeyError):
        del_obj_at_key_path(o, ['a', 0, 'a', 0, 1])

    # Now destroy the object
    del_obj_at_key_path(o, ['a', 0, 'a'])
    assert o == {'a': [{}]}
    del_obj_at_key_path(o, ['a', 0])
    assert o == {'a': []}
    del_obj_at_key_path(o, ['a'])
    assert o == {}


def test_get_obj_at_key_path():
    o = {'a': [{'a': [1, 2, 3]}]}
    o1 = get_obj_at_key_path(o, ['a', 0, 'a', 0])
    assert o1 == 1

    o2 = get_obj_at_key_path(o, ['a', 0, 'a'])
    assert o2 == [1, 2, 3]

    o3 = get_obj_at_key_path(o, ['a', 0])
    assert o3 == {'a': [1, 2, 3]}

    o4 = get_obj_at_key_path(o, ['a'])
    assert o4 == [{'a': [1, 2, 3]}]

    o5 = get_obj_at_key_path(o, [])
    assert o5 == o

    o6 = get_obj_at_key_path(o, ['a', '123'])
    assert o6 is None


def test_set_obj_at_key_path():
    o = {'a': [{'a': [1, 2, 3]}]}
    original_o = {'a': [{'a': [1, 2, 3]}]}

    with pytest.raises(KeyError):
        set_obj_at_key_path(o, ['a', '1234'], 42)
    o = set_obj_at_key_path(o, ['a', '1234'], 42, False)
    assert o == original_o

    with pytest.raises(KeyError):
        set_obj_at_key_path(o, ['a', 1234], 42)
    o = set_obj_at_key_path(o, ['a', 1234], 42, False)
    assert o == original_o

    with pytest.raises(KeyError):
        set_obj_at_key_path(o, ['a', 0, 'd', 10, 11, 12], 42)
    o = set_obj_at_key_path(o, ['a', 0, 'd', 10, 11, 12], 42, False)
    assert o == original_o

    o = set_obj_at_key_path(o, ['a', 0, 'a', 0], 42)
    assert o['a'][0]['a'][0] == 42
    o = set_obj_at_key_path(o, ['a', 0, 'a'], 42)
    assert o['a'][0]['a'] == 42
    o = set_obj_at_key_path(o, ['a', 0], 42)
    assert o['a'][0] == 42
    o = set_obj_at_key_path(o, ['a'], 42)
    assert o['a'] == 42
    o = set_obj_at_key_path(o, [], 42)
    assert o == 42


def test_get_conf_set_for_key_path():
    expected = set(['d', 'd.e', 'd.e.f'])
    actual = get_conf_set_for_key_path(
        set(['a.b.c.d', 'a.b.c.d.e', 'a.b.c.d.e.f',
             'd', 'd.e', 'd.e.f']), ('a', 'b', 'c'))
    assert actual == expected


def test_remove_prefix_value_error():
    with pytest.raises(ValueError):
        remove_prefix('a.b.c.d.e', 'a.b.c.e')


@pytest.mark.parametrize('value, expected', [
    (None, [None]),
    ('foo', ['foo']),
    (('foo', 'bar'), ['foo', 'bar']),
    (['foo', 'bar'], ['foo', 'bar'])
])
def test_force_list(value, expected):
    result = force_list(value)
    assert result == expected
