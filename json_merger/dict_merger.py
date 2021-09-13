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

import copy
import logging

import six
from dictdiffer import ADD, CHANGE, REMOVE, patch
from dictdiffer.merge import Merger, UnresolvedConflictsException

from .config import DictMergerOps
from .conflict import Conflict, ConflictType
from .errors import MergeError
from .nothing import NOTHING
from .utils import (
    dedupe_list, del_obj_at_key_path, get_dotted_key_path, get_obj_at_key_path,
    set_obj_at_key_path
)

LOGGER = logging.getLogger(__name__)


def _get_list_fields(obj, res, key_path=()):
    if isinstance(obj, list):
        res.append(key_path)
    elif isinstance(obj, dict):
        for key, value in six.iteritems(obj):
            _get_list_fields(value, res, key_path + (key, ))

    return res


def patch_to_conflict_set(patch):
    """Translates a dictdiffer conflict into a json_merger one."""
    patch_type, patched_key, value = patch
    if isinstance(patched_key, list):
        key_path = tuple(patched_key)
    else:
        key_path = tuple(k for k in patched_key.split('.') if k)

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
    """3-way Merger that ignores list fields."""

    def __init__(self, root, head, update, default_op,
                 data_lists=None, custom_ops={}, key_path=None):
        self.root = copy.deepcopy(root)
        self.head = copy.deepcopy(head)
        self.update = copy.deepcopy(update)
        self.custom_ops = custom_ops
        self.default_op = self._operation_to_function(default_op)
        self.data_lists = set(data_lists or [])
        self.key_path = key_path or []

        # We can have the same conflict appear more times because we keep only
        # one of the possible resolutions as a conflict while we apply the
        # other as a fallback. Sometimes multiple fallback dict diffs
        # conflict with a single change.
        self.conflict_set = set()
        self.skipped_lists = set()
        self.merged_root = None
        self.list_backups = {}

    def _build_skipped_lists(self):
        lists = set()
        lists.update(_get_list_fields(self.head, []))
        lists.intersection_update(_get_list_fields(self.update, []))
        for list_ in lists:
            dotted = get_dotted_key_path(list_, True)
            if dotted not in self.data_lists:
                self.skipped_lists.add(list_)

    def _backup_lists(self):
        self._build_skipped_lists()
        for list_ in self.skipped_lists:
            self.list_backups[list_] = (
                get_obj_at_key_path(self.root, list_),
                get_obj_at_key_path(self.head, list_),
                get_obj_at_key_path(self.update, list_))
            # The root is the only one that may not be there. Head and update
            # are retrieved using list intersection.
            del_obj_at_key_path(self.root, list_, False)
            del_obj_at_key_path(self.head, list_)
            del_obj_at_key_path(self.update, list_)

    def _restore_lists(self):
        for list_, (bak_r, bak_h, bak_u) in six.iteritems(self.list_backups):
            if bak_r is not None:
                set_obj_at_key_path(self.root, list_, bak_r)
            set_obj_at_key_path(self.head, list_, bak_h)
            set_obj_at_key_path(self.update, list_, bak_u)

    @property
    def conflicts(self):
        """List of conflicts for the current object."""

        # Make this compatible with the project convention (list of conflicts).
        return list(self.conflict_set)

    def _merge_base_values(self):
        if self.head == self.update:
            self.merged_root = self.head
        elif self.head == NOTHING:
            self.merged_root = self.update
        elif self.update == NOTHING:
            self.merged_root = self.head
        elif self.head == self.root:
            self.merged_root = self.update
        elif self.update == self.root:
            self.merged_root = self.head
        else:
            strategy = self._get_rule_for_field(self.key_path)
            self.merged_root, conflict = {
                'f': (self.head, self.update),
                's': (self.update, self.head)}[strategy]
            self.conflict_set.add(
                Conflict(ConflictType.SET_FIELD, (), conflict))

    def _merge_dicts(self):
        self._backup_lists()

        LOGGER.debug(
            "Merging dicts with root=%s, head=%s, update=%s",
            self.root,
            self.head,
            self.update,
        )
        non_list_merger = Merger(self.root, self.head, self.update, {})
        try:
            non_list_merger.run()
        except UnresolvedConflictsException as e:
            self._solve_dict_conflicts(non_list_merger, e.content)

        self._restore_lists()
        remove_patches = []
        other_patches = []
        for patch_ in non_list_merger.unified_patches:
            if patch_[0] == 'remove':
                remove_patches.append(patch_)
            else:
                other_patches.append(patch_)
        remove_patches_deduped = dedupe_list(remove_patches)
        unified_patches = remove_patches_deduped + other_patches
        self.merged_root = patch(
                unified_patches,
                self.root
            )

    def _solve_dict_conflicts(self, non_list_merger, conflicts):
        strategies = [self._get_custom_strategy(conflict)
                      for conflict in conflicts]
        non_list_merger.continue_run(strategies)

        for conflict, strategy in zip(conflicts, strategies):
            conflict_patch = {'f': conflict.second_patch,
                              's': conflict.first_patch}[strategy]
            conflict_set = patch_to_conflict_set(conflict_patch)
            LOGGER.debug(
                "Solved conflict using strategy %s, conflicts=%s",
                strategy,
                conflict_set,
            )
            self.conflict_set.update(conflict_set)

    def _get_custom_strategy(self, patch):
        full_path = self._get_path_from_patch(patch)
        return self._get_rule_for_field(full_path)

    @staticmethod
    def _get_path_from_patch(patch):
        _, field, modification = patch.first_patch

        full_path = []
        if isinstance(field, list):
            full_path.extend(field)
        elif field:
            full_path.append(field)

        if (isinstance(modification, list) and modification[0][0]):
            full_path.append(modification[0][0])

        return full_path

    @staticmethod
    def _operation_to_function(operation):
        if callable(operation):
            return operation
        elif operation == DictMergerOps.FALLBACK_KEEP_HEAD:
            return lambda head, update, down_path: 'f'
        elif operation == DictMergerOps.FALLBACK_KEEP_UPDATE:
            return lambda head, update, down_path: 's'
        else:
            return lambda head, update, down_path: None

    def _absolute_path(self, field_path):
        full_path = list(self.key_path) + field_path
        return get_dotted_key_path(full_path, filter_int_keys=True)

    def _get_rule_for_field(self, field_path):
        current_path = self._absolute_path(field_path)
        head = get_obj_at_key_path(self.head, field_path)
        update = get_obj_at_key_path(self.update, field_path)
        down_path = []
        rule = None

        while current_path:
            operation = self._operation_to_function(
                self.custom_ops.get(current_path)
            )
            rule = operation(head, update, down_path)
            if rule:
                break
            current_path_parts = current_path.split('.')
            current_path = '.'.join(current_path_parts[:-1])
            down_path.append(current_path_parts[-1])

        return rule or self.default_op(head, update, field_path)

    def merge(self):
        """Perform merge of head and update starting from root."""
        if isinstance(self.head, dict) and isinstance(self.update, dict):
            if not isinstance(self.root, dict):
                self.root = {}
            self._merge_dicts()
        else:
            self._merge_base_values()

        if self.conflict_set:
            raise MergeError('Dictdiffer Errors', self.conflicts)
