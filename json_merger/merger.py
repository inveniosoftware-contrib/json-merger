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

from dictdiffer import patch
from dictdiffer.merge import Merger, UnresolvedConflictsException

from .comparator import DefaultComparator
from .errors import MergeError
from .list_unify import ListUnifier, UnifierOps
from .nothing import NOTHING


def _get_list_fields(obj, res, key_path=()):
    if isinstance(obj, list):
        res.append(key_path)
    elif isinstance(obj, dict):
        for key, value in obj.iteritems():
            _get_list_fields(value, res, key_path + (key, ))

    return res


def _get_obj_at_key_path(obj, key_path):
    current = obj
    for k in key_path:
        current = current[k]
    return current


def _set_obj_at_key_path(obj, key_path, value):
    obj = _get_obj_at_key_path(obj, key_path[:-1])
    obj[key_path[-1]] = value


def _nothing_to_base_type(src_obj, target_obj):
    if src_obj != NOTHING:
        return src_obj
    if isinstance(target_obj, dict):
        return {}
    if isinstance(target_obj, list):
        return []
    if isinstance(target_obj, basestring):
        return ''
    if isinstance(target_obj, (int, long, float, complex)):
        return 0


def _translate_nothing_objects(*args):
    typed_obj = [a for a in args if a != NOTHING][0]
    return (_nothing_to_base_type(a, typed_obj) for a in args)


class ListAlignMerger(object):

    def __init__(self, root, head, update, default_op,
                 comparators=None, ops=None):
        self.comparators = comparators or {}
        self.default_op = default_op
        self.ops = ops or {}

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

    def _backup_lists(self, root, head, update, list_key_paths):
        list_backups = {}
        for l in list_key_paths:
            list_backups[l] = (_get_obj_at_key_path(root, l),
                               _get_obj_at_key_path(head, l),
                               _get_obj_at_key_path(update, l))
            _set_obj_at_key_path(root, l, None)
            _set_obj_at_key_path(head, l, None)
            _set_obj_at_key_path(update, l, None)
        return list_backups

    def _restore_lists(self, root, head, update, list_backups):
        for l, (bak_r, bak_h, bak_u) in list_backups.iteritems():
            _set_obj_at_key_path(root, l, bak_r)
            _set_obj_at_key_path(head, l, bak_h)
            _set_obj_at_key_path(update, l, bak_u)

    def _recursive_merge(self, root, head, update, key_path=()):
        common_lists = set(_get_list_fields(root, []))
        common_lists.intersection_update(set(_get_list_fields(head, [])))
        common_lists.intersection_update(set(_get_list_fields(update, [])))

        list_backups = self._backup_lists(root, head, update, common_lists)
        non_list_merger = Merger(root, head, update, {})

        try:
            non_list_merger.run()
        except UnresolvedConflictsException as e:
            # TODO resolve conflict paths to key_path
            self.conflicts.extend(e.content)

        if hasattr(non_list_merger, 'unified_patches'):
            # TODO do it correctly
            root = patch(non_list_merger.unified_patches, root)

        self._restore_lists(root, head, update, list_backups)

        for list_field in common_lists:
            absolute_key_path = key_path + list_field
            dotted_key_path = '.'.join(absolute_key_path)

            root_l = _get_obj_at_key_path(root, list_field)
            head_l = _get_obj_at_key_path(head, list_field)
            update_l = _get_obj_at_key_path(update, list_field)

            operation = self.ops.get(dotted_key_path, self.default_op)
            comparator = self.comparators.get(dotted_key_path,
                                              DefaultComparator())
            list_unifier = ListUnifier(root_l, head_l, update_l,
                                       operation, comparator)
            try:
                list_unifier.unify()
            except MergeError as e:
                self.conflicts.extend(e.content)

            new_root_list = []
            for root_obj, head_obj, update_obj in list_unifier.unified:
                root_obj, head_obj, update_obj = _translate_nothing_objects(
                    root_obj, head_obj, update_obj)

                # Intentionally skip list index in key path as ops and
                # comparators do not contain list index keys.
                new_obj = self._recursive_merge(root_obj, head_obj, update_obj,
                                                absolute_key_path)
                new_root_list.append(new_obj)

            _set_obj_at_key_path(root, list_field, new_root_list)

        return root


class UpdateMerger(ListAlignMerger):

    def __init__(self, root, head, update, comparators=None, ops=None):
        super(UpdateMerger, self).__init__(
                root, head, update, UnifierOps.KEEP_ONLY_UPDATE_ENTITIES,
                comparators, ops)
