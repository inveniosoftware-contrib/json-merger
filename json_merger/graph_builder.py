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

from .comparator import DefaultComparator
from .errors import MergeError
from .nothing import NOTHING


class OrderGraphBuilder(object):

    def __init__(self, root, head, update, sources, comparator=None):
        self.root = root
        self.head = head
        self.update = update
        self.comparator = comparator or DefaultComparator()
        self.sources = sources

        self.graph = {}
        self.node_data = {}

        self._node_src_indices = {}
        self._head_idx_to_node = {}
        self._update_idx_to_node = {}

        self._next_node_id = 0

    def _new_node_id(self):
        node_id = self._next_node_id
        self._next_node_id += 1
        return node_id

    def _push_node(self, root_elem, head_elem, update_elem):
        root_idx, root_obj = root_elem
        head_idx, head_obj = head_elem
        update_idx, update_obj = update_elem

        node_id = self._new_node_id()
        self.node_data[node_id] = (root_obj, head_obj, update_obj)
        self._node_src_indices[node_id] = (root_idx, head_idx, update_idx)

        if head_idx >= 0:
            self._head_idx_to_node[head_idx] = node_id
        if update_idx >= 0:
            self._update_idx_to_node[update_idx] = node_id

    def _get_matching_element(self, target, obj):
        matches = [(i, o) for i, o in enumerate(target)
                   if self.comparator.equal(o, obj)]
        if len(matches) > 1:
            # Can't do anything with multiple matches.
            # TODO find a meaningful content
            raise MergeError('fixme', None)
        return matches[0] if matches else (-1, NOTHING)

    def _populate_nodes(self):
        if 'head' in self.sources:
            for head_idx, head_obj in enumerate(self.head):
                head_elem = (head_idx, head_obj)
                root_elem = self._get_matching_element(self.root, head_obj)
                update_elem = self._get_matching_element(self.update, head_obj)

                self._push_node(root_elem, head_elem, update_elem)

        if 'update' in self.sources:
            for update_idx, update_obj in enumerate(self.update):
                # Already added this node in the graph, continue.
                if update_idx in self._update_idx_to_node:
                    continue

                update_elem = (update_idx, update_obj)
                root_elem = self._get_matching_element(self.root, update_obj)
                head_elem = self._get_matching_element(self.head, update_obj)

                self._push_node(root_elem, head_elem, update_elem)

    def build_graph(self):
        self._populate_nodes()

        for node_id, node_indices in self._node_src_indices.iteritems():
            root_idx, head_idx, update_idx = node_indices
            head_prev = head_idx - 1
            update_prev = update_idx - 1

            self.graph[node_id] = set()
            if (head_prev in self._head_idx_to_node and
                    'head' in self.sources):
                self.graph[node_id].add(self._head_idx_to_node[head_prev])
            if (update_prev in self._update_idx_to_node and
                    'update' in self.sources):
                self.graph[node_id].add(self._update_idx_to_node[update_prev])

        return self.graph, self.node_data
