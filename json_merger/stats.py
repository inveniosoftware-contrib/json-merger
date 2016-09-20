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


class ListMatchStats(object):
    """Class for holding list entity matching stats."""

    def __init__(self, lst, root):
        """
        Args:
            lst: The list of elements that needs to be matched.
            root: The ancestor of the list of elements that needs to be
                  matched.

        Attributes:
            in_result_idx: Indices of elements in lst that are present in the
                end result.

            in_result: Elements in lst that are present in the end result.

            not_in_result_idx: Indices of elements in lst that are not present
                in the end result.

            not_in_result: Elements in lst that are not present in the end
                result.

            not_in_result_root_match_idx: Indices of elements that are not in
                the end result but were matched with root elements.

            not_in_result_root_match: Elements that are not in the end result
                but were matched with root elements.

            not_in_result_not_root_match_idx: Indices of elements that are not
                in the end result and were not matched with any root elements.

            not_in_result_not_root_match: Elements that are not in the end
                result and were not matched with any root elements.

            not_in_result_root_match_pairs: Pairs of (lst, root) elements
                that are not in the end result but were matched.
        """
        self.lst = lst
        self.root = root

        self.in_result_idx = set()
        self.not_in_result_root_match_idx = set()
        self.root_matches = {}

    def move_to_result(self, lst_idx):
        """Moves element from lst available at lst_idx."""
        self.in_result_idx.add(lst_idx)

        if lst_idx in self.not_in_result_root_match_idx:
            self.not_in_result_root_match_idx.remove(lst_idx)

    def add_root_match(self, lst_idx, root_idx):
        """Adds a match for the elements avaialble at lst_idx and root_idx."""
        self.root_matches[lst_idx] = root_idx
        if lst_idx in self.in_result_idx:
            return

        self.not_in_result_root_match_idx.add(lst_idx)

    @property
    def not_in_result_idx(self):
        return set(range(len(self.lst))).difference(self.in_result_idx)

    @property
    def not_in_result_not_root_match_idx(self):
        return self.not_in_result_idx.difference(
            self.not_in_result_root_match_idx)

    @property
    def in_result(self):
        return [self.lst[e] for e in self.in_result_idx]

    @property
    def not_in_result(self):
        return [self.lst[e] for e in self.not_in_result_idx]

    @property
    def not_in_result_root_match(self):
        return [self.lst[e] for e in self.not_in_result_root_match_idx]

    @property
    def not_in_result_not_root_match(self):
        return [self.lst[e] for e in self.not_in_result_not_root_match_idx]

    @property
    def not_in_result_root_match_pairs(self):
        return [(self.lst[e], self.root[self.root_matches[e]])
                for e in self.not_in_result_root_match_idx]

    @property
    def not_matched_root_objects(self):
        matched_root_idx = set(self.root_matches.values())
        return [o for idx, o in enumerate(self.root)
                if idx not in matched_root_idx]
