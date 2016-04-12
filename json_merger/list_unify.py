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

from .comparator import DefaultComparator
from .errors import MergeError
from .graph_builder import (
    ListMatchGraphBuilder, toposort, sort_cyclic_graph_best_effort)
from .nothing import NOTHING

_OPERATIONS = [
    'KEEP_ONLY_HEAD_ENTITIES',
    'KEEP_ONLY_UPDATE_ENTITIES',
    'KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST',
    'KEEP_UPDATE_AND_HEAD_ENTITIES_UPDATE_FIRST',
    'KEEP_UPDATE_ENTITIES_CONFLICT_ON_HEAD_DELETE'
]


class UnifierOps(object):
    pass

for mode in _OPERATIONS:
    setattr(UnifierOps, mode, mode)

_SOURCES = {
    UnifierOps.KEEP_ONLY_UPDATE_ENTITIES: ['update'],
    UnifierOps.KEEP_ONLY_HEAD_ENTITIES: ['head'],
    UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST: ['update', 'head'],
    UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_UPDATE_FIRST: ['update', 'head'],
    UnifierOps.KEEP_UPDATE_ENTITIES_CONFLICT_ON_HEAD_DELETE: ['update']
}

_PICK_FIRST = {
    UnifierOps.KEEP_ONLY_UPDATE_ENTITIES: 'update',
    UnifierOps.KEEP_ONLY_HEAD_ENTITIES: 'head',
    UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST: 'head',
    UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_UPDATE_FIRST: 'update',
    UnifierOps.KEEP_UPDATE_ENTITIES_CONFLICT_ON_HEAD_DELETE: 'update'
}

_RAISE_ERROR_OPS = [
    UnifierOps.KEEP_UPDATE_ENTITIES_CONFLICT_ON_HEAD_DELETE
]


class ListUnifier(object):

    def __init__(self, root, head, update, operation, comparator=None):
        if operation not in _OPERATIONS:
            raise ValueError('Operation %r not permitted' % operation)

        self.root = root
        self.head = head
        self.update = update
        self.comparator = comparator or DefaultComparator()

        # Wether to raise error on deleting a head entity.
        # TODO implement this
        self.raise_on_head_delete = operation in _RAISE_ERROR_OPS
        # Sources from which to keep entities.
        self.sources = _SOURCES[operation]
        # Source from which to pick the first element when they can be
        # interchanged in the topological sort.
        self.pick_first = _PICK_FIRST[operation]

        self.unified = []

    def unify(self):
        graph_builder = ListMatchGraphBuilder(
            self.root, self.head, self.update, self.sources, self.comparator)
        # TODO check for multiple match exceptions and do something about it.
        graph, nodes = graph_builder.build_graph()

        try:
            node_order = toposort(graph, self.pick_first)
        except ValueError:
            node_order = sort_cyclic_graph_best_effort(graph, self.pick_first)
            raise MergeError('Check Order', [])
        finally:
            for node in node_order:
                self.unified.append(nodes[node])
