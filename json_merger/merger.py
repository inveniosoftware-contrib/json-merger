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

from .comparator import DefaultComparator
from .dict_merger import SkipListsMerger
from .errors import MergeError
from .list_unify import ListUnifier, UnifierOps
from .nothing import NOTHING
from .utils import get_obj_at_key_path, set_obj_at_key_path


def _translate_nothing_objects(*args):
    typed_obj = [a for a in args if a != NOTHING][0]
    return (_nothing_to_base_type(a, typed_obj) for a in args)


def _nothing_to_base_type(src_obj, target_obj):
    if src_obj != NOTHING:
        return src_obj
    if isinstance(target_obj, dict):
        return {}
    if isinstance(target_obj, list):
        return []
    return None


def _get_config_key_path(absolute_key_path):
    return '.'.join(a for a in absolute_key_path if not isinstance(a, int))


class ListAlignMerger(object):

    def __init__(self, root, head, update, default_op,
                 comparators=None, ops=None, dict_merger_kwargs=None):
        self.comparators = comparators or {}
        self.default_op = default_op
        self.ops = ops or {}
        self.dict_merger_kwargs = dict_merger_kwargs or {}

        self.root = copy.deepcopy(root)
        self.head = copy.deepcopy(head)
        self.update = copy.deepcopy(update)

        self.conflicts = []
        self.merged_root = None

    def merge(self):
        self.merged_root = self._recursive_merge(self.root, self.head,
                                                 self.update)
        if self.conflicts:
            raise MergeError('Conflicts Occured in Merge Process',
                             self.conflicts)

    def _recursive_merge(self, root, head, update, key_path=()):
        non_list_merger = SkipListsMerger(root, head, update,
                                          **self.dict_merger_kwargs)
        try:
            non_list_merger.merge()
        except MergeError as e:
            self.conflicts.extend(c.with_prepended_path(key_path)
                                  for c in e.content)

        root = non_list_merger.merged_root

        for list_field in non_list_merger.skipped_lists:
            absolute_key_path = key_path + list_field
            dotted_key_path = _get_config_key_path(absolute_key_path)

            operation = self.ops.get(dotted_key_path, self.default_op)
            comparator = self.comparators.get(dotted_key_path,
                                              DefaultComparator())
            root_l = get_obj_at_key_path(root, list_field, [])
            head_l = get_obj_at_key_path(head, list_field, [])
            update_l = get_obj_at_key_path(update, list_field, [])

            list_unifier = ListUnifier(root_l, head_l, update_l,
                                       operation, comparator)
            try:
                list_unifier.unify()
            except MergeError as e:
                self.conflicts.extend(c.with_prepended_path(absolute_key_path)
                                      for c in e.content)

            new_root_list = []
            for idx, objects in enumerate(list_unifier.unified):
                root_obj, head_obj, update_obj = _translate_nothing_objects(
                    *objects)

                new_obj = self._recursive_merge(root_obj, head_obj, update_obj,
                                                absolute_key_path + (idx, ))
                new_root_list.append(new_obj)

            set_obj_at_key_path(root, list_field, new_root_list)

        return root


class UpdateMerger(ListAlignMerger):

    def __init__(self, root, head, update, comparators=None, ops=None):
        super(UpdateMerger, self).__init__(
                root, head, update, UnifierOps.KEEP_ONLY_UPDATE_ENTITIES,
                comparators, ops)
