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

"""Module that is able to merge JSON record objects."""

from __future__ import absolute_import, print_function

import copy

from .comparator import DefaultComparator
from .dict_merger import DictMergerOps, SkipListsMerger
from .errors import MergeError
from .list_unify import ListUnifier, UnifierOps
from .utils import (
    get_conf_set_for_key_path, get_dotted_key_path, get_obj_at_key_path,
    set_obj_at_key_path
)

PLACEHOLDER_STR = "#$PLACEHOLDER$#"


class ListAlignMerger(object):

    def __init__(self, root, head, update,
                 default_dict_merge_op, default_list_merge_op,
                 list_merge_ops=None, comparators=None, data_lists=None):
        self.comparators = comparators or {}
        self.data_lists = set(data_lists or [])
        self.list_merge_ops = list_merge_ops or {}

        self.default_dict_merge_op = default_dict_merge_op
        self.default_list_merge_op = default_list_merge_op

        self.root = copy.deepcopy(root)
        self.head = copy.deepcopy(head)
        self.update = copy.deepcopy(update)
        self.head_stats = {}
        self.update_stats = {}

        self.conflicts = []
        self.merged_root = None

        self.aligned_root = copy.deepcopy(root)
        self.aligned_head = copy.deepcopy(head)
        self.aligned_update = copy.deepcopy(update)

    def merge(self):
        self.merged_root = self._recursive_merge(self.root, self.head,
                                                 self.update)
        if self.conflicts:
            raise MergeError('Conflicts Occured in Merge Process',
                             self.conflicts)

    def _merge_objects(self, root, head, update, key_path):
        data_lists = get_conf_set_for_key_path(self.data_lists, key_path)
        object_merger = SkipListsMerger(root, head, update,
                                        self.default_dict_merge_op, data_lists)
        try:
            object_merger.merge()
        except MergeError as e:
            self.conflicts.extend(c.with_prefix(key_path) for c in e.content)
        return object_merger

    def _build_aligned_lists_and_stats(self, list_unifier, key_path):
        root_list = []
        head_list = []
        update_list = []
        for root_obj, head_obj, update_obj in list_unifier.unified:
            # Cast NOTHING objects to a placeholder so we reserialize back to
            # JSON if needed.
            root_list.append(root_obj or PLACEHOLDER_STR)
            head_list.append(head_obj or PLACEHOLDER_STR)
            update_list.append(update_obj or PLACEHOLDER_STR)

        # If we can't set that key path a list to be merged wasn't there
        # In the first place.
        self.aligned_root = set_obj_at_key_path(self.aligned_root,
                                                key_path, root_list, False)
        self.aligned_head = set_obj_at_key_path(self.aligned_head,
                                                key_path, head_list, False)
        self.aligned_update = set_obj_at_key_path(self.aligned_update,
                                                  key_path, update_list, False)
        self.head_stats[key_path] = list_unifier.head_stats
        self.update_stats[key_path] = list_unifier.update_stats

    def _unify_lists(self, root, head, update, key_path):
        dotted_key_path = get_dotted_key_path(key_path, True)

        operation = self.list_merge_ops.get(dotted_key_path,
                                            self.default_list_merge_op)
        comparator_cls = self.comparators.get(dotted_key_path,
                                              DefaultComparator)
        list_unifier = ListUnifier(root, head, update,
                                   operation, comparator_cls)
        try:
            list_unifier.unify()
        except MergeError as e:
            self.conflicts.extend(c.with_prefix(key_path) for c in e.content)

        return list_unifier

    def _recursive_merge(self, root, head, update, key_path=()):
        dotted_key_path = get_dotted_key_path(key_path, True)
        if (isinstance(head, list) and isinstance(update, list) and
                dotted_key_path not in self.data_lists):
            # We are aligning bare lists so the key path is an empty tuple.
            lists = [()]
            if not isinstance(root, list):
                root = []
        else:
            m = self._merge_objects(root, head, update, key_path)
            root = m.merged_root
            lists = m.skipped_lists

        for list_field in lists:
            absolute_key_path = key_path + list_field

            root_l = get_obj_at_key_path(root, list_field, [])
            head_l = get_obj_at_key_path(head, list_field, [])
            update_l = get_obj_at_key_path(update, list_field, [])

            unifier = self._unify_lists(root_l, head_l, update_l,
                                        absolute_key_path)

            new_list = []
            for idx, objects in enumerate(unifier.unified):
                root_obj, head_obj, update_obj = objects
                new_obj = self._recursive_merge(root_obj, head_obj, update_obj,
                                                absolute_key_path + (idx, ))
                new_list.append(new_obj)

            root = set_obj_at_key_path(root, list_field, new_list)
            self._build_aligned_lists_and_stats(unifier, absolute_key_path)

        return root


class UpdateMerger(ListAlignMerger):

    def __init__(self, root, head, update,
                 list_merge_ops=None, comparators=None, data_lists=None):
        super(UpdateMerger, self).__init__(
                root, head, update,
                DictMergerOps.FALLBACK_KEEP_HEAD_CONFLICT,
                UnifierOps.KEEP_ONLY_UPDATE_ENTITIES,
                list_merge_ops, comparators, data_lists)
