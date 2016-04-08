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


class ListUnifyException(Exception):

    def __init__(self, message, content):
        super(ListUnifyException, self).__init__(message)
        self.content = content


class ListUnifier(object):

    KEEP_ONLY_UPDATE_ENTITIES = 0
    KEEP_ONLY_HEAD_ENTITIES = 1
    KEEP_UPDATE_AND_HEAD_ENTITIES_UPDATE_ORDER = 2
    KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_ORDER = 3
    KEEP_UPDATE_ENTITIES_CONFLICT_ON_HEAD_DELETE = 4
    # TODO increase this when others are correctly implemented.
    _LAST_OP = 1

    def __init__(self, root, head, update, comparator, operation):
        if operation >= self._LAST_OP:
            raise ValueError('Operation %r not permitted' % operation)

        self.root = root
        self.head = head
        self.update = update
        self.comparator = comparator

        self.raise_on_head_delete = False
        self.sources = []
        self._parse_operation(operation)
        self.unified = []

    def _parse_operation(self, operation):
        self.sources = {
            self.KEEP_ONLY_UPDATE_ENTITIES: [self.update],
            self.KEEP_ONLY_HEAD_ENTITIES: [self.head],
            self.KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_ORDER: [self.update,
                                                            self.head],
            self.KEEP_UPDATE_AND_HEAD_ENTITIES_UPDATE_ORDER: [self.update,
                                                              self.head],
            self.KEEP_UPDATE_ENTITIES_CONFLICT_ON_HEAD_DELETE: [self.update],
        }[operation]

        if operation in [self.KEEP_UPDATE_ENTITIES_CONFLICT_ON_HEAD_DELETE]:
            self.raise_on_head_delete = True

    def _get_matching_element(self, target, obj):
        matches = [o for o in target if self.comparator.equal(o, obj)]
        if len(matches) > 1:
            # TODO raise in the end
            raise ListUnifyException('fixme', None)
        return matches[0] if matches else {}

    def unify(self):
        # TODO implement in generic way using sources.
        for update_obj in self.update:
            root_obj = self._get_matching_element(self.root, update_obj)
            head_obj = self._get_matching_element(self.head, update_obj)
            self.unified.append((root_obj, head_obj, update_obj))
