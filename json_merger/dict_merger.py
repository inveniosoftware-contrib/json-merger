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

import six

from dictdiffer import patch, ADD, CHANGE, REMOVE
from dictdiffer.merge import Merger, UnresolvedConflictsException

from .conflict import Conflict, ConflictType
from .errors import MergeError
from .utils import (
    del_obj_at_key_path, get_obj_at_key_path, set_obj_at_key_path)


def _get_list_fields(obj, res, key_path=()):
    if isinstance(obj, list):
        res.append(key_path)
    elif isinstance(obj, dict):
        for key, value in six.iteritems(obj):
            _get_list_fields(value, res, key_path + (key, ))

    return res


def patch_to_conflict_set(patch):
    """Translate a dictdiffer conflict into a json_merger one."""
    patch_type, dotted_key, value = patch
    key_path = tuple([k for k in dotted_key.split('.') if k])

    conflicts = set()
    if patch_type == REMOVE:
        conflict_type = ConflictType.REMOVE_FIELD
        for key, obj in value:
            conflicts.add(Conflict(conflict_type, key_path + (key, ), None))
    elif patch_type == CHANGE:
        conflict_type = ConflictType.SET_FIELD
        first_val, second_val = value
        conflicts.add(Conflict(conflict_type, key_path, second_val))
    elif patch_type == ADD:
        conflict_type = ConflictType.SET_FIELD
        for key, obj in value:
            conflicts.add(Conflict(conflict_type, key_path + (key, ), obj))

    return conflicts


class SkipListsMerger(object):

    def __init__(self, root, head, update, keep='head',
                 raise_on_conflict=True):
        self.root = root
        self.head = head
        self.update = update
        self.pick = 'f' if keep == 'head' else 's'
        self.raise_on_conflict = raise_on_conflict

        # We can have the same conflict appear more times because we keep only
        # one of the possible resolutions as a conflict while we apply the
        # other as a fallback. Sometimes multiple fallback dict diffs
        # conflict with a single change.
        self.conflict_set = set()
        self.skipped_lists = set()
        self.merged_root = None
        self.list_backups = {}

    def _backup_lists(self):
        for l in self.skipped_lists:
            self.list_backups[l] = (
                get_obj_at_key_path(self.root, l),
                get_obj_at_key_path(self.head, l),
                get_obj_at_key_path(self.update, l))
            # The root is the only one that may not be there. Head and update
            # are retrieved using list intersection.
            del_obj_at_key_path(self.root, l, False)
            del_obj_at_key_path(self.head, l)
            del_obj_at_key_path(self.update, l)

    def _restore_lists(self):
        for l, (bak_r, bak_h, bak_u) in six.iteritems(self.list_backups):
            if bak_r is not None:
                set_obj_at_key_path(self.root, l, bak_r)
            set_obj_at_key_path(self.head, l, bak_h)
            set_obj_at_key_path(self.update, l, bak_u)

    @property
    def conflicts(self):
        """List of conflicts for the current object."""

        # Make this compatible with the project convention (list of conflicts).
        return list(self.conflict_set)

    def merge(self):
        self.skipped_lists.update(_get_list_fields(self.head, []))
        self.skipped_lists.intersection_update(
            _get_list_fields(self.update, []))

        list_backups = self._backup_lists()
        non_list_merger = Merger(self.root, self.head, self.update, {})

        try:
            non_list_merger.run()
        except UnresolvedConflictsException as e:
            non_list_merger.continue_run([self.pick
                                          for i in range(len(e.content))])
            for conflict in e.content:
                conflict_patch = {'f': conflict.second_patch,
                                  's': conflict.first_patch}[self.pick]
                self.conflict_set.update(patch_to_conflict_set(conflict_patch))

        self._restore_lists()

        self.merged_root = patch(non_list_merger.unified_patches, self.root)

        if self.raise_on_conflict and self.conflict_set:
            raise MergeError('Dictdiffer Errors', self.conflicts)
