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

from collections import deque

import six

from .comparator import DefaultComparator
from .nothing import NOTHING
from .stats import ListMatchStats

FIRST = 'first'


class BeforeNodes(object):
    """Edge in the match graph."""

    def __init__(self, head_node=None, update_node=None):
        self.head_node = head_node
        self.update_node = update_node

    def __repr__(self):
        return 'BeforeNodes <head_node: {}, update_node: {}>'.format(
            self.head_node, self.update_node)


class ListMatchGraphBuilder(object):

    def __init__(self, root, head, update, sources,
                 comparator_cls=DefaultComparator):
        self.root = root
        self.head = head
        self.update = update
        self.sources = sources

        self.root_head_comparator = comparator_cls(self.root, self.head)
        self.root_update_comparator = comparator_cls(self.root, self.update)
        self.head_update_comparator = comparator_cls(self.head, self.update)

        # Keys are (target, source), values are comparator_instance and
        # the source list from which to search.
        self.comparators = {
            ('root', 'head'): (self.root_head_comparator, 'l2'),
            ('head', 'root'): (self.root_head_comparator, 'l1'),
            ('root', 'update'): (self.root_update_comparator, 'l2'),
            ('update', 'root'): (self.root_update_comparator, 'l1'),
            ('head', 'update'): (self.head_update_comparator, 'l2'),
            ('update', 'head'): (self.head_update_comparator, 'l1'),
        }

        self.node_data = {}
        self.graph = {}
        self.head_stats = ListMatchStats(head, root)
        self.update_stats = ListMatchStats(update, root)

        self._node_src_indices = {}
        self._head_idx_to_node = {}
        self._update_idx_to_node = {}
        self._dirty_nodes = set()

        self._next_node_id = 0

        self.multiple_match_choice_idx = set()
        self.multiple_match_choices = []

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

    def _get_matches(self, source, source_idx, source_obj):
        other_two = {'head': ['root', 'update'],
                     'update': ['root', 'head'],
                     'root': ['head', 'update']}
        indices = {'root': {}, 'head': {}, 'update': {}}
        indices[source][source_idx] = source_obj

        # Start a BFS of matching elements.
        q = deque([(source, source_idx)])
        while q:
            curr_src, curr_idx = q.popleft()
            for target in other_two[curr_src]:
                comparator, cmp_list = self.comparators[(target, curr_src)]
                # cmp_list is either 'l1' or 'l2'
                # (the paremeter for the comparator class convetion)
                matches = comparator.get_matches(cmp_list, curr_idx)
                for target_idx, target_obj in matches:
                    if target_idx in indices[target]:
                        continue
                    indices[target][target_idx] = target_obj
                    q.append((target, target_idx))
        result = {}
        for lst, res_indices in indices.items():
            if not res_indices:
                result[lst] = [(-1, NOTHING)]
            else:
                result[lst] = sorted(res_indices.items())

        return result['root'], result['head'], result['update']

    def _add_matches(self, root_elems, head_elems, update_elems):
        matches = [(r, h, u)
                   for r in root_elems
                   for h in head_elems
                   for u in update_elems]
        if len(matches) == 1:
            self._push_node(*matches[0])
        else:
            self.multiple_match_choice_idx.update([(r[0], h[0], u[0])
                                                   for r, h, u in matches])

    def _populate_nodes(self):
        for idx, obj in enumerate(self.head):
            r_elems, h_elems, u_elems = self._get_matches('head', idx, obj)
            if 'head' in self.sources:
                self._add_matches(r_elems, h_elems, u_elems)
            if len(r_elems) == 1 and r_elems[0][0] >= 0:
                self.head_stats.add_root_match(idx, r_elems[0][0])

        for idx, obj in enumerate(self.update):
            r_elems, h_elems, u_elems = self._get_matches('update', idx, obj)
            # Only add the node to the graph only if not already added.
            if ('update' in self.sources and
                    idx not in self._update_idx_to_node):
                self._add_matches(r_elems, h_elems, u_elems)
            if len(r_elems) == 1 and r_elems[0][0] >= 0:
                self.update_stats.add_root_match(idx, r_elems[0][0])

        # Add stats from built nodes.
        for root_idx, head_idx, update_idx in self._node_src_indices.values():
            if head_idx >= 0:
                self.head_stats.move_to_result(head_idx)
            if update_idx >= 0:
                self.update_stats.move_to_result(update_idx)

        # Move the unique multiple match indices to conflicts.
        for r_idx, h_idx, u_idx in self.multiple_match_choice_idx:
            r_obj = self.root[r_idx] if r_idx >= 0 else None
            h_obj = self.head[h_idx] if h_idx >= 0 else None
            u_obj = self.update[u_idx] if u_idx >= 0 else None
            self.multiple_match_choices.append((r_obj, h_obj, u_obj))

    def _get_next_node(self, source, indices):
        if source not in self.sources:
            return None
        idx_to_node = {
            'head': self._head_idx_to_node,
            'update': self._update_idx_to_node
        }[source]
        for idx in indices:
            if idx in idx_to_node:
                return idx_to_node[idx]
        return None

    def build_graph(self):
        self._populate_nodes()

        # Link a dummy first node before the first element of the sources
        # lists.
        self.node_data[FIRST] = (NOTHING, NOTHING, NOTHING)
        self.graph[FIRST] = BeforeNodes()

        next_head_node = self._get_next_node('head', range(len(self.head)))
        next_update_node = self._get_next_node('update',
                                               range(len(self.update)))
        self.graph[FIRST].head_node = next_head_node
        self.graph[FIRST].update_node = next_update_node

        # Link any other nodes with the elements that come after them in their
        # source lists.
        for node_id, node_indices in six.iteritems(self._node_src_indices):
            root_idx, head_idx, update_idx = node_indices
            head_next_l = []
            update_next_l = []
            if head_idx >= 0:
                head_next_l = range(head_idx + 1, len(self.head))
            if update_idx >= 0:
                update_next_l = range(update_idx + 1, len(self.update))

            next_head_node = self._get_next_node('head', head_next_l)
            next_update_node = self._get_next_node('update', update_next_l)
            self.graph[node_id] = BeforeNodes(next_head_node, next_update_node)

        return self.graph, self.node_data


def _get_traversal(next_nodes, pick_first):
    if pick_first == 'head':
        return [next_nodes.update_node, next_nodes.head_node]
    else:
        return [next_nodes.head_node, next_nodes.update_node]


def toposort(graph, pick_first='head'):
    """Toplogically sorts a list match graph.

    Tries to perform a topological sort using as tiebreaker the pick_first
    argument. If the graph contains cycles, raise ValueError.
    """
    in_deg = {}
    for node, next_nodes in six.iteritems(graph):
        for next_node in [next_nodes.head_node, next_nodes.update_node]:
            if next_node is None:
                continue
            in_deg[next_node] = in_deg.get(next_node, 0) + 1

    stk = [FIRST]
    ordered = []
    visited = set()
    while stk:
        node = stk.pop()
        visited.add(node)
        if node != FIRST:
            ordered.append(node)
        traversal = _get_traversal(graph.get(node, BeforeNodes()), pick_first)
        for next_node in traversal:
            if next_node is None:
                continue
            if next_node in visited:
                raise ValueError('Graph has a cycle')

            in_deg[next_node] -= 1
            if in_deg[next_node] == 0:
                stk.append(next_node)

    # Nodes may not be walked because they don't reach in degree 0.
    if len(ordered) != len(graph) - 1:
        raise ValueError('Graph has a cycle')
    return ordered


def sort_cyclic_graph_best_effort(graph, pick_first='head'):
    """Fallback for cases in which the graph has cycles."""
    ordered = []
    visited = set()
    # Go first on the pick_first chain then go back again on the others
    # that were not visited. Given the way the graph is built both chains
    # will always contain all the elements.
    if pick_first == 'head':
        fst_attr, snd_attr = ('head_node', 'update_node')
    else:
        fst_attr, snd_attr = ('update_node', 'head_node')

    current = FIRST
    while current is not None:
        visited.add(current)
        current = getattr(graph[current], fst_attr)
        if current not in visited and current is not None:
            ordered.append(current)
    current = FIRST
    while current is not None:
        visited.add(current)
        current = getattr(graph[current], snd_attr)
        if current not in visited and current is not None:
            ordered.append(current)
    return ordered
