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

from toposort import toposort

class ListUnifyException(Exception):

    def __init__(self, message, content):
        super(ListUnifyException, self).__init__(message)
        self.content = content


class OrderGraphBuilder(object):
    # TODO TODO TODO TODO do something about the default value

    def __init__(self, root, head, update, comparator, sources):
        self.root = root
        self.head = head
        self.update = update
        self.comparator = comparator
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
            raise ListUnifyException('fixme', None)
        return matches[0] if matches else (-1, None)

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


class ListUnifier(object):

    KEEP_ONLY_UPDATE_ENTITIES = 0
    KEEP_ONLY_HEAD_ENTITIES = 1
    KEEP_UPDATE_AND_HEAD_ENTITIES_UPDATE_FIRST = 2
    KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST = 3
    KEEP_UPDATE_ENTITIES_CONFLICT_ON_HEAD_DELETE = 4
    # TODO increase this when others are correctly implemented.
    _LAST_OP = 5

    def __init__(self, root, head, update, comparator, operation):
        if operation >= self._LAST_OP:
            raise ValueError('Operation %r not permitted' % operation)

        self.root = root
        self.head = head
        self.update = update
        self.comparator = comparator

        # TODO what this shit means!
        self.raise_on_head_delete = False
        self.sources = []
        self.pick_first = None
        self._parse_operation(operation)

        self.unified = []

    def _parse_operation(self, operation):
        self.sources = {
            self.KEEP_ONLY_UPDATE_ENTITIES: ['update'],
            self.KEEP_ONLY_HEAD_ENTITIES: ['head'],
            self.KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST: ['update', 'head'],
            self.KEEP_UPDATE_AND_HEAD_ENTITIES_UPDATE_FIRST: ['update',
                                                              'head'],
            self.KEEP_UPDATE_ENTITIES_CONFLICT_ON_HEAD_DELETE: ['update']
        }[operation]

        self.pick_first = {
            self.KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST: 'head'
        }.get(operation, 'update')

        if operation in [self.KEEP_UPDATE_ENTITIES_CONFLICT_ON_HEAD_DELETE]:
            self.raise_on_head_delete = True

    def unify(self):
        graph_builder = OrderGraphBuilder(self.root, self.head, self.update,
                                          self.comparator, self.sources)
        graph, nodes = graph_builder.build_graph()
        ordered = toposort(graph)

        head_id = 1
        update_id = 2
        for node_set in ordered:
            head_nodes = [nodes[n] for n in node_set
                          if nodes[n][head_id] and not nodes[n][update_id]]
            update_nodes = [nodes[n] for n in node_set
                            if not nodes[n][head_id] and nodes[n][update_id]]
            common_nodes = [nodes[n] for n in node_set
                            if nodes[n][head_id] and nodes[n][update_id]]
            if self.pick_first == 'head':
                self.unified.extend(head_nodes)
                self.unified.extend(common_nodes)
                self.unified.extend(update_nodes)
            else:
                self.unified.extend(update_nodes)
                self.unified.extend(common_nodes)
                self.unified.extend(head_nodes)

