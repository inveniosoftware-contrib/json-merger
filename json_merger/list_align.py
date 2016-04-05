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

"""Module for aligning the same entities in lists."""

from __future__ import absolute_import, print_function

import copy

from munkres import Munkres


class Nothing(object):

    def __eq__(self, other):
        if isinstance(other, Nothing):
            return True
        return False

    def __ne__(self, other):
        if isinstance(other, Nothing):
            return False
        return True


# Create a new placeholder for None objects that doesn't conflict with None
# entries in the dicts.
NOTHING = Nothing()


class MergerError(Exception):
    pass


class DefaultComparator(object):

    def distance(self, obj1, obj2):
        return 0 if obj1 == obj2 else 1

    def equal(self, obj1, obj2):
        return obj1 == obj2


class ComparatorWrapper(object):

    def __init__(self, wrapped):
        self.wrapped = wrapped

    def distance(self, obj1, obj2):
        if all([o == NOTHING for o in [obj1, obj2]]):
            return 0
        if any([o == NOTHING for o in [obj1, obj2]]):
            return 1
        return self.wrapped.distance(obj1, obj2)

    def equal(self, obj1, obj2):
        if all([o == NOTHING for o in [obj1, obj2]]):
            return True
        if any([o == NOTHING for o in [obj1, obj2]]):
            return False
        return self.wrapped.equal(obj1, obj2)


class ListAligner(object):
    UPDATE = 'update'
    ENRICH = 'enrich'

    def __init__(self, comparators=None):
        # TODO ValueErrors
        if not comparators:
            self.comparators = {}
        else:
            self.comparators = comparators

    def align_lists(self, src, update, mode):
        """Merge update upon src."""
        src = copy.deepcopy(src)
        update = copy.deepcopy(update)

        if mode == self.UPDATE:
            # In UPDATE mode preserve all entities and the order from update.
            self._deep_match_lists([], src, update)
        elif mode == self.ENRICH:
            # In ENRICH mode preserve all entities and the order from src.
            self._deep_match_lists([], update, src)

        return src, update

    def _deep_match_lists(self, key_path, src, dst):
        if isinstance(src, list) and isinstance(dst, list):
            # This will be always called over same length lists.
            keys = range(len(src))
            append_key = False
        elif isinstance(src, dict) and isinstance(dst, dict):
            keys = set(src.keys()).intersection(dst.keys())
            append_key = True
        else:
            return

        for k in keys:
            if append_key:
                key_path.append(k)

            if isinstance(src[k], list) and isinstance(dst[k], list):
                l1, l2 = self._match_lists(key_path, src[k], dst[k])
                src[k] = l1
                dst[k] = l2
                # With the same objects aligned merge their internal lists.
                self._deep_match_lists(key_path, src[k], dst[k])
            else:
                self._deep_match_lists(key_path, src[k], dst[k])

    def _match_lists(self, key_path, src, dst):
        new_len = max(len(src), len(dst))
        self._pad_with_nothing(src, new_len)
        self._pad_with_nothing(dst, new_len)

        dotted_key = '.'.join(key_path)
        comparator = ComparatorWrapper(self.comparators.get(
            dotted_key,
            DefaultComparator()))

        cost_matrix = [[comparator.distance(x, y) for y in src] for x in dst]

        new_src = []
        new_dst = []

        solver = Munkres()
        # Preserve the order of objects from the destination object.
        for dst_idx, src_idx in solver.compute(cost_matrix):
            if not comparator.equal(src[src_idx], dst[dst_idx]):
                # Matching source entry is not equal to the destination.
                # This means that the matching source entry was deleted and
                # the destination entry is completly new.
                new_src.append(NOTHING)
                new_dst.append(dst[dst_idx])
            else:
                new_src.append(src[src_idx])
                new_dst.append(dst[dst_idx])
        return new_src, new_dst

    def _pad_with_nothing(self, lst, length):
        pad_len = length - len(lst)
        if pad_len < 0:
            return
        lst.extend([NOTHING] * pad_len)

    def filter_nothing_objs(self, obj):
        if isinstance(obj, dict):
            keys = obj.keys()
        elif isinstance(obj, list):
            keys = range(len(obj))
        else:
            return

        for k in keys:
            if isinstance(obj[k], list):
                obj[k] = [o for o in obj[k] if o != NOTHING]
            self.filter_nothing_objs(obj[k])
