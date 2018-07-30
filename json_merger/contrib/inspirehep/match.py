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

from munkres import Munkres


def distance_function_match(l1, l2, thresh, dist_fn, norm_funcs=[]):
    """Returns pairs of matching indices from l1 and l2."""
    common = []
    # We will keep track of the global index in the source list as we
    # will successively reduce their sizes.
    l1 = list(enumerate(l1))
    l2 = list(enumerate(l2))

    # Use the distance function and threshold on hints given by normalization.
    # See _match_by_norm_func for implementation details.
    # Also wrap the list element function function to ignore the global list
    # index computed above.
    for norm_fn in norm_funcs:
        new_common, l1, l2 = _match_by_norm_func(
                l1, l2,
                lambda a: norm_fn(a[1]),
                lambda a1, a2: dist_fn(a1[1], a2[1]),
                thresh)
        # Keep only the global list index in the end result.
        common.extend((c1[0], c2[0]) for c1, c2 in new_common)

    # Take any remaining umatched entries and try to match them using the
    # Munkres algorithm.
    dist_matrix = [[dist_fn(e1, e2) for i2, e2 in l2] for i1, e1 in l1]

    # Call Munkres on connected components on the remaining bipartite graph.
    # An edge links an element from l1 with an element from l2 only if
    # the distance between the elements is less (or equal) than the theshold.
    components = BipartiteConnectedComponents()
    for l1_i in range(len(l1)):
        for l2_i in range(len(l2)):
            if dist_matrix[l1_i][l2_i] > thresh:
                continue
            components.add_edge(l1_i, l2_i)

    for l1_indices, l2_indices in components.get_connected_components():
        # Build a partial distance matrix for each connected component.
        part_l1 = [l1[i] for i in l1_indices]
        part_l2 = [l2[i] for i in l2_indices]

        part_dist_matrix = [[dist_matrix[l1_i][l2_i] for l2_i in l2_indices]
                            for l1_i in l1_indices]
        part_cmn = _match_munkres(part_l1, part_l2, part_dist_matrix, thresh)

        common.extend((c1[0], c2[0]) for c1, c2 in part_cmn)

    return common


def _match_by_norm_func(l1, l2, norm_fn, dist_fn, thresh):
    """Matches elements in l1 and l2 using normalization functions.

    Splits the elements in each list into buckets given by the normalization
    function. If the same normalization value points to a bucket from the
    first list and a bucket from the second list, both with a single element
    we consider the elements in the list as matching if the distance between
    them is less (or equal) than the threshold.

    e.g. l1 = ['X1', 'Y1', 'Y2', 'Z5'], l2 = ['X1', 'Y3', 'Z1']
         norm_fn = lambda x: x[0]
         dist_fn = lambda e1, e2: 0 if e1 == e2 else 1
         thresh = 0

    The buckets will then be:
        l1_bucket = {'X': ['X1'], 'Y': ['Y1', 'Y2'], 'Z': ['Z5']}
        l2_bucket = {'X': ['X1'], 'Y': ['Y3'], 'Z': ['Z1']}

    For each normalized value:
        'X' -> consider 'X1' equal with 'X1' since the distance is equal with
               the thershold
        'Y' -> skip the lists since we have multiple possible matches
        'Z' -> consider 'Z1' and 'Z5' as different since the distance is
               greater than the threshold.
    Return:
        [('X1', 'X2')]
    """
    common = []

    l1_only_idx = set(range(len(l1)))
    l2_only_idx = set(range(len(l2)))

    buckets_l1 = _group_by_fn(enumerate(l1), lambda x: norm_fn(x[1]))
    buckets_l2 = _group_by_fn(enumerate(l2), lambda x: norm_fn(x[1]))

    for normed, l1_elements in buckets_l1.items():
        l2_elements = buckets_l2.get(normed, [])
        if not l1_elements or not l2_elements:
            continue
        _, (_, e1_first) = l1_elements[0]
        _, (_, e2_first) = l2_elements[0]
        match_is_ambiguous = not (
            len(l1_elements) == len(l2_elements) and (
                all(e2 == e2_first for (_, (_, e2)) in l2_elements) or
                all(e1 == e1_first for (_, (_, e1)) in l1_elements)
            )
        )
        if match_is_ambiguous:
            continue
        for (e1_idx, e1), (e2_idx, e2) in zip(l1_elements, l2_elements):
            if dist_fn(e1, e2) > thresh:
                continue
            l1_only_idx.remove(e1_idx)
            l2_only_idx.remove(e2_idx)
            common.append((e1, e2))

    l1_only = [l1[i] for i in l1_only_idx]
    l2_only = [l2[i] for i in l2_only_idx]

    return common, l1_only, l2_only


def _match_munkres(l1, l2, dist_matrix, thresh):
    """Matches two lists using the Munkres algorithm.

    Returns pairs of matching indices from the two lists by minimizing the sum
    of the distance between the linked elements and taking only the elements
    which have the distance between them less (or equal) than the threshold.
    """
    equal_dist_matches = set()
    m = Munkres()
    indices = m.compute(dist_matrix)

    for l1_idx, l2_idx in indices:
        dst = dist_matrix[l1_idx][l2_idx]
        if dst > thresh:
            continue
        for eq_l2_idx, eq_val in enumerate(dist_matrix[l1_idx]):
            if abs(dst - eq_val) < 1e-9:
                equal_dist_matches.add((l1_idx, eq_l2_idx))
        for eq_l1_idx, eq_row in enumerate(dist_matrix):
            if abs(dst - eq_row[l2_idx]) < 1e-9:
                equal_dist_matches.add((eq_l1_idx, l2_idx))

    return [(l1[l1_idx], l2[l2_idx]) for l1_idx, l2_idx in equal_dist_matches]


class BipartiteConnectedComponents(object):
    """Union-Find implementation for getting connected components."""

    def __init__(self):
        self.parents = {}

    def add_edge(self, p1_node, p2_node):
        node_1 = (p1_node, None)
        node_2 = (None, p2_node)
        self._union(node_1, node_2)

    def get_connected_components(self):
        components_by_root = _group_by_fn(self.parents.keys(),
                                          self._find)
        for root in components_by_root:
            components_by_root[root].append(root)

        for component in components_by_root.values():
            p1_nodes = []
            p2_nodes = []
            for p1_node, p2_node in component:
                if p1_node is None:
                    p2_nodes.append(p2_node)
                if p2_node is None:
                    p1_nodes.append(p1_node)
            yield (p1_nodes, p2_nodes)

    def _union(self, node_1, node_2):
        parent_1 = self._find(node_1)
        parent_2 = self._find(node_2)
        if parent_1 != parent_2:
            self.parents[parent_1] = parent_2

    def _find(self, node):
        root = node
        while root in self.parents:
            root = self.parents[root]
        while node in self.parents:
            prev_node = node
            node = self.parents[node]
            self.parents[prev_node] = root
        return root


def _group_by_fn(iterable, fn):
    buckets = {}
    for elem in iterable:
        key = fn(elem)
        if key not in buckets:
            buckets[key] = []
        buckets[key].append(elem)
    return buckets
