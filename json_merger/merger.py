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

"""Definition for JSON merger class."""

from __future__ import absolute_import, print_function

import copy

from .comparator import DefaultComparator
from .dict_merger import SkipListsMerger
from .errors import MergeError
from .list_unify import ListUnifier
from .utils import (
    get_conf_set_for_key_path, get_dotted_key_path, get_obj_at_key_path,
    set_obj_at_key_path
)

PLACEHOLDER_STR = '#$PLACEHOLDER$#'


class Merger(object):
    """Class that merges two JSON objects that share a common ancestor.

    This class treats by default all lists as being lists of entities and
    offers support for matching their elements by their content, by specifing
    per-field comparator classes.
    """

    def __init__(self, root, head, update,
                 default_dict_merge_op, default_list_merge_op,
                 list_dict_ops=None, list_merge_ops=None,
                 comparators=None, data_lists=None):
        """
        Args:
            root: A common ancestor of the two objects being merged.

            head: One of the objects that is being merged. Refers to the
                version that is currently in use. (e.g. a displayed database
                record)

            update: The second object that is being merged. Refers to an update
                that needs to be integrated with the in-use version.

            default_dict_merge_op
              (:class:`json_merger.config.DictMergerOps` class attribute):
                Default strategy for merging regular non list JSON values
                (strings, numbers, other objects).

            default_list_merge_op
              (:class:`json_merger.config.UnifierOps` class attribute):
                Default strategy for merging two lists of entities.

            dict_merge_ops: Defines custom strategies for merging dict of
                entities.

                Dict formatted as:
                    * keys -- a config string
                    * values -- a class attribute of
                      :class:`json_merger.config.DictMergerOps`

            list_merge_ops: Defines custom strategies for merging lists of
                entities.

                Dict formatted as:
                    * keys -- a config string
                    * values -- a class attribute of
                      :class:`json_merger.config.UnifierOps`

            comparators: Defines classes used for rendering entities in list
                fields as equal.

                Dict formatted as:
                    * keys -- a config string
                    * values -- a class that extends
                      :class:`json_merger.comparator.BaseComparator`

            data_lists: List of config strings defining the lists that are not
                treated as lists of entities.

        Note:
            A configuration string represents the path towards a list field in
            the object sepparated with dots.

        Example:
            Configuration strings can be:

                For ``{'lst': [{'id': 0, 'tags': ['foo', 'bar']}]}``:

                * the config string for the top level list is ``'lst'``
                * the config string for the tags lists is ``'lst.tags'``
        """
        self.comparators = comparators or {}
        self.data_lists = set(data_lists or [])
        self.list_dict_ops = list_dict_ops or {}
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
        """Populates result members.

        Performs the merge algorithm using the specified config and fills in
        the members that provide stats about the merging procedure.

        Attributes:
            merged_root: The result of the merge.

            aligned_root, aligned_head, aligned_update: Copies of root, head
                and update in which all matched list entities have the same
                list index for easier diff viewing.

            head_stats, update_stats: Stats for each list field present in the
                head or update objects. Instance of
                :class:`json_merger.stats.ListMatchStats`

            conflicts: List of :class:`json_merger.conflict.Conflict` instances
                that occured during the merge.

        Raises:
            :class:`json_merger.errors.MergeError` : If conflicts occur during
                the call.

        Example:
            >>> from json_merger import Merger
            >>> # We compare people by their name
            >>> from json_merger.comparator import PrimaryKeyComparator
            >>> from json_merger.config import DictMergerOps, UnifierOps
            >>> from json_merger.errors import MergeError
            >>> # Use this only for doctest :)
            >>> from pprint import pprint as pp
            >>>
            >>> root = {'people': [{'name': 'Jimmy', 'age': 30}]}
            >>> head = {'people': [{'name': 'Jimmy', 'age': 31},
            ...                    {'name': 'George'}]}
            >>> update = {'people': [{'name': 'John'},
            ...                      {'name': 'Jimmy', 'age': 32}]}
            >>>
            >>> class NameComparator(PrimaryKeyComparator):
            ...     # Two objects are the same entitity if they have the
            ...     # same name.
            ...     primary_key_fields = ['name']
            >>> m = Merger(root, head, update,
            ...            DictMergerOps.FALLBACK_KEEP_HEAD,
            ...            UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST,
            ...            comparators = {'people': NameComparator})
            >>> # We do a merge
            >>> try:
            ...     m.merge()
            ... except MergeError as e:
            ...     # Conflicts are the same thing as the exception content.
            ...     assert e.content == m.conflicts
            >>> # This is how the lists are aligned:
            >>> pp(m.aligned_root['people'], width=60)
            ['#$PLACEHOLDER$#',
             {'age': 30, 'name': 'Jimmy'},
             '#$PLACEHOLDER$#']
            >>> pp(m.aligned_head['people'], width=60)
            ['#$PLACEHOLDER$#',
             {'age': 31, 'name': 'Jimmy'},
             {'name': 'George'}]
            >>> pp(m.aligned_update['people'], width=60)
            [{'name': 'John'},
             {'age': 32, 'name': 'Jimmy'},
             '#$PLACEHOLDER$#']
            >>> # This is the end result of the merge:
            >>> pp(m.merged_root, width=60)
            {'people': [{'name': 'John'},
                        {'age': 31, 'name': 'Jimmy'},
                        {'name': 'George'}]}
            >>> # With some conflicts:
            >>> pp(m.conflicts, width=60)
            [('SET_FIELD', ('people', 1, 'age'), 32)]
            >>> # And some stats:
            >>> pp(m.head_stats[('people',)].in_result)
            [{'age': 31, 'name': 'Jimmy'}, {'name': 'George'}]
            >>> pp(m.update_stats[('people',)].not_in_result)
            []

        Note:
            Even if conflicts occur, merged_root, aligned_root, aligned_head
            and aligned_update are always populated by following the
            startegies set for the merger instance.
        """
        self.merged_root = self._recursive_merge(self.root, self.head,
                                                 self.update)
        if self.conflicts:
            raise MergeError('Conflicts Occurred in Merge Process',
                             self.conflicts)

    def _recursive_merge(self, root, head, update, key_path=()):
        dotted_key_path = get_dotted_key_path(key_path, filter_int_keys=True)

        if (isinstance(head, list) and isinstance(update, list) and
                dotted_key_path not in self.data_lists):
            # In this case we are merging two lists of objects.
            lists_to_unify = [()]
            if not isinstance(root, list):
                root = []
        else:
            # Otherwise we merge everything but the lists using DictMergerOps.
            m = self._merge_objects(root, head, update, key_path)
            root = m.merged_root
            lists_to_unify = m.skipped_lists

        for list_field in lists_to_unify:
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

    def _merge_objects(self, root, head, update, key_path):
        data_lists = get_conf_set_for_key_path(self.data_lists, key_path)

        object_merger = SkipListsMerger(root, head, update,
                                        self.default_dict_merge_op,
                                        data_lists, self.list_dict_ops,
                                        key_path)

        try:
            object_merger.merge()
        except MergeError as e:
            self.conflicts.extend(c.with_prefix(key_path) for c in e.content)

        return object_merger

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

        # Try to put back the list if the key path existed in the first place.
        self.aligned_root = set_obj_at_key_path(self.aligned_root,
                                                key_path, root_list, False)
        self.aligned_head = set_obj_at_key_path(self.aligned_head,
                                                key_path, head_list, False)
        self.aligned_update = set_obj_at_key_path(self.aligned_update,
                                                  key_path, update_list, False)

        # Also copy over the stats.
        self.head_stats[key_path] = list_unifier.head_stats
        self.update_stats[key_path] = list_unifier.update_stats
