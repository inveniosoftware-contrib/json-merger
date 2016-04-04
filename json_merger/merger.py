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

"""Invenio module that is able to merge json record objects."""

from __future__ import absolute_import, print_function

import copy

from dictdiffer import REMOVE, diff, patch
from munkres import Munkres, print_matrix


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


class Merger(object):

    def __init__(self, config, distance_fn=lambda x, y: 0 if x == y else 1):
        self.allow_removes_from = set(config.get('ALLOW_REMOVES_FROM', []))
        self.distance_fn = distance_fn
        return not self == other


# Create a new placeholder for None objects that doesn't conflict with None
# entries in the dicts.
NOTHING = Nothing()


class MergerError(Exception):
    pass


class Merger(object):

    def __init__(self, config, distance_fn=lambda x, y: 0 if x == y else 1):
        self.allow_removes_from = set(config.get('ALLOW_REMOVES_FROM', []))
        self.distance_fn = distance_fn

    def merge_records(self, src, update):
        """Merge update upon src."""
        src = copy.deepcopy(src)
        update = copy.deepcopy(update)
        self._deep_match_lists([], src, update)

        changes = []
        for change_type, key_path, value in diff(src, update):
            if change_type == REMOVE:
                # We use this only on JSONs so any int key is a list index,
                # which our config ignores.
                conf_key_path = [k for k in key_path if not isinstance(k, int)]
                new_value = []
                for removed_key, removed_obj in value:
                    removed_full_key = '.'.join(conf_key_path + [removed_key])
                    if removed_full_key in self.allow_removes_from:
                        new_value.append((removed_key, removed_obj))
                if new_value:
                    changes.append((REMOVE, conf_key_path, new_value))
            else:
                changes.append((change_type, key_path, value))

        new_src = patch(changes, src)
        self._filter_nothing_objs(new_src)

        return new_src

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
                # The lists should always have the same length.
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
        cost_matrix = [[self.distance_fn(x, y) for y in src] for x in dst]
        new_src = []
        new_dst = []

        solver = Munkres()
        # Preserve the order of objects from the destination object.
        for dst_idx, src_idx in solver.compute(cost_matrix):
            if cost_matrix[dst_idx][src_idx] > 0:
                # We are introducing a new object so we match it with a dummy
                # NOTHING entry in the src side.
                new_src.append(NOTHING)
                new_dst.append(dst[dst_idx])
                if '.'.join(key_path) not in self.allow_removes_from:
                    # If we don't want to remove the object in the list, add
                    # the same object in the new destination so the dictdiff.
                    # will be clean for this particular index.
                    new_src.append(src[src_idx])
                    new_dst.append(src[src_idx])
            else:
                new_src.append(src[src_idx])
                new_dst.append(dst[dst_idx])
        return new_src, new_dst

    def _pad_with_nothing(self, lst, length):
        pad_len = length - len(lst)
        if pad_len < 0:
            return
        lst.extend([NOTHING] * pad_len)

    def _filter_nothing_objs(self, obj):
        if isinstance(obj, dict):
            keys = obj.keys()
        elif isinstance(obj, list):
            keys = range(len(obj))
        else:
            return

        for k in keys:
            if isinstance(obj[k], list):
                obj[k] = [o for o in obj[k] if o != NOTHING]
            self._filter_nothing_objs(obj[k])
