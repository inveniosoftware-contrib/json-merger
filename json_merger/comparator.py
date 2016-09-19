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

from __future__ import absolute_import, print_function

from .nothing import NOTHING
from .utils import get_obj_at_key_path


class BaseComparator(object):
    """Abstract base class for Entity Comparison."""

    def __init__(self, l1, l2):
        """
        Args:
            l1: First list of entities.
            l2: Second list of entities.
        """
        self.l1 = l1
        self.l2 = l2
        self.matches = set()
        self.process_lists()

    def process_lists(self):
        """Do any preprocessing of the lists."""
        for l1_idx, obj1 in enumerate(self.l1):
            for l2_idx, obj2 in enumerate(self.l2):
                if self.equal(obj1, obj2):
                    self.matches.add((l1_idx, l2_idx))

    def equal(self, obj1, obj2):
        """Implementation of object equality."""
        raise NotImplementedError()

    def get_matches(self, src, src_idx):
        """Get elements equal to the idx'th in src from the other list.

        e.g. get_matches(self, 'l1', 0) will return all elements from self.l2
        matching with self.l1[0]
        """
        if src not in ('l1', 'l2'):
            raise ValueError('Must have one of "l1" or "l2" as src')
        if src == 'l1':
            target_list = self.l2
        else:
            target_list = self.l1
        comparator = {
            'l1': lambda s_idx, t_idx: (s_idx, t_idx) in self.matches,
            'l2': lambda s_idx, t_idx: (t_idx, s_idx) in self.matches,
        }[src]

        return [(trg_idx, obj) for trg_idx, obj in enumerate(target_list)
                if comparator(src_idx, trg_idx)]


class PrimaryKeyComparator(BaseComparator):
    """Considers two objects as equal if they have the same primary key.

    If two objects have at least one of the configured primary_key_fields equal
    then they are equal. A primary key field can be any of:

    string: Two objects are equal if the values at the given key paths
            are equal. Example:
                For 'key1.key2' the objects are equal if
                obj1['key1']['key2'] == obj2['key1']['key2'].
    list: Two objects are equal if all the values at the key paths
          in the list are equal. Example:
                For ['key1', 'key2.key3'] the objects are equal if
                obj1['key1'] == obj2['key1'] and
                obj1['key2']['key3'] == obj2['key2']['key3'].

    For normalizing the fields in the objects to be compared, one can add
    a normalization function for each field in the normalization_functions
    dict.

    Example:
        Setting the normalization_functions field to:
            ``{'key1': str.lower}``
        would normalize
            obj1 = {'key1': 'ID123'} and obj2 = {'key1': 'id123'} to
            obj1 = {'key1': 'id123'} and obj2 = {'key1': 'id123'}
    """

    primary_key_fields = ['pk']
    normalization_functions = {}

    def _have_field_equal(self, obj1, obj2, field):
        key_path = tuple(k for k in field.split('.') if k)
        o1 = get_obj_at_key_path(obj1, key_path, NOTHING)
        o2 = get_obj_at_key_path(obj2, key_path, NOTHING)
        if o1 == NOTHING or o2 == NOTHING:
            return False

        fn = self.normalization_functions.get(field, lambda x: x)
        return fn(o1) == fn(o2)

    def equal(self, obj1, obj2):
        if obj1 == obj2:
            return True

        for field_set in self.primary_key_fields:
            if not isinstance(field_set, list):
                field_set = [field_set]
            checks = [self._have_field_equal(obj1, obj2, field)
                      for field in field_set]
            if all(checks):
                return True

        return False


class DefaultComparator(BaseComparator):
    """Two objects are the same entity if they are fully equal."""

    def equal(self, obj1, obj2):
        return obj1 == obj2
