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
import six

from dictdiffer import ADD, CHANGE, REMOVE, patch
from dictdiffer.merge import Merger, UnresolvedConflictsException

from .config import DictMergerOps
from .conflict import Conflict, ConflictType
from .errors import MergeError
from .nothing import NOTHING
from .utils import (
    del_obj_at_key_path, get_dotted_key_path, get_obj_at_key_path,
    set_obj_at_key_path
)


def _get_list_fields(obj, res, key_path=()):
    if isinstance(obj, list):
        res.append(key_path)
    elif isinstance(obj, dict):
        for key, value in six.iteritems(obj):
            _get_list_fields(value, res, key_path + (key, ))

    return res


def patch_to_conflict_set(patch):
    """Translates a dictdiffer conflict into a json_merger one."""
    patch_type, dotted_key, value = patch
    key_path = tuple(k for k in dotted_key.split('.') if k)

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
        self.pick = {DictMergerOps.FALLBACK_KEEP_HEAD: 'f',
                     DictMergerOps.FALLBACK_KEEP_UPDATE: 's'}[default_op]
        self.data_lists = set(data_lists or [])
        self.key_path = key_path

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
        for l in lists:
            dotted = get_dotted_key_path(l, True)
            if dotted not in self.data_lists:
                self.skipped_lists.add(l)

    def _backup_lists(self):
        self._build_skipped_lists()
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
            self.merged_root, conflict = {
                'f': (self.head, self.update),
                's': (self.update, self.head)}[self.pick]
            self.conflict_set.add(
                Conflict(ConflictType.SET_FIELD, (), conflict))

    def _merge_dicts(self):
        self._backup_lists()

        non_list_merger = Merger(self.root, self.head, self.update, {})
        try:
            non_list_merger.run()
        except UnresolvedConflictsException as e:
            self._solve_dict_conflict(non_list_merger, e)

        self._restore_lists()
        self.merged_root = patch(non_list_merger.unified_patches, self.root)

    def _solve_dict_conflict(self, non_list_merger, e):
        continue_list = self._get_custom_strategies(
            e.content
        )
        non_list_merger.continue_run(continue_list)
        for i in range(len(e.content)):
            conflict = e.content[i]
            strategy = continue_list[i]

            conflict_patch = {'f': conflict.second_patch,
                              's': conflict.first_patch}[strategy]

            self.conflict_set.update(patch_to_conflict_set(conflict_patch))

    def _get_custom_strategies(self, patches):
        strategies = []
        for patch in patches:
            head = patch.first_patch

            field = ''
            if head[1]:
                field = head[1]
            elif head[2][0][0]:
                field = head[2][0][0]

            strategies.append(
                self._get_related_path(field)
            )

        return strategies

    def _get_path(self, custom_path):
        if self.custom_ops.get(custom_path, None):
            return {
                DictMergerOps.FALLBACK_KEEP_HEAD: 'f',
                DictMergerOps.FALLBACK_KEEP_UPDATE: 's'
            }[self.custom_ops[custom_path]]
        return None

    def _composed_rule_extract(self, list_path):
        """This functions extracts custom rules for nested objects.

        Example:
            'authors': 1,
            'authors.affiliations': 2,
            'authors.affiliations.value': 3,

            >>> _composed_rule_extract(['authors','affiliation', 'value']) == 3
            >>> True
            >>> _composed_rule_extract(['authors']) == 1
            >>> True

        """
        while list_path:
            curr_dotted_path = '.'.join(list_path)
            rule = self._get_path(curr_dotted_path)
            if rule:
                return rule
            list_path.pop()
        return None

    def _obj_from_keypath(self, key_path, path):
        """
        Given a key_path list object, returns a list
        representing the object structure

         Example:
             path = 'value'
             key_path = ['authors', 0, 'affiliations', 0]

             return ['authors','affiliations', 'value']
         """
        curr_path = [
            item for item in key_path if isinstance(item, six.string_types)
        ]
        curr_path.append(path)
        return curr_path

    def _get_related_path(self, path):
        """
            Transform `path` object, which can be a string or a list, into a
            list that will be used to retrieve custom rules for the given path.
        """
        if isinstance(path, list):
            list_path = path[:-1]
        else:
            list_path = path.split('.')

        # handling objects without lists
        rule = self._composed_rule_extract(list_path)
        if rule:
            return rule

        # handling objects with lists
        if self.key_path:
            rule = self._composed_rule_extract(
                self._obj_from_keypath(self.key_path, path)
            )

        # in case of no match, keep default rule
        return rule if rule else self.pick

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
