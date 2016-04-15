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


class BaseComparator(object):

    def __init__(self, l1, l2):
        self.l1 = l1
        self.l2 = l2
        self.process_lists()

    def process_lists(self):
        """Do any preprocessing of the lists."""
        pass

    def equal(self, idx_l1, idx_l2):
        raise NotImplementedError()

    def get_matches(self, src, src_idx):
        """Get elements equal to the idx'th in src from the other list.

        e.g. get_matches(self, 'l1', 0) will return all elements from self.l2
        matching with self.l1[0]
        """
        if src not in ('l1', 'l2'):
            raise ValueError('Must have one of "l1" or "l2" as src')
        if src == 'l1':
            source_list = self.l1
            target_list = self.l2
        else:
            source_list = self.l2
            target_list = self.l1
        comparator = {
            'l1': lambda s_idx, t_idx: self.equal(s_idx, t_idx),
            'l2': lambda s_idx, t_idx: self.equal(t_idx, s_idx)
        }[src]

        return [(trg_idx, obj) for trg_idx, obj in enumerate(target_list)
                if comparator(src_idx, trg_idx)]


class DefaultComparator(BaseComparator):

    def equal(self, idx_l1, idx_l2):
        return self.l1[idx_l1] == self.l2[idx_l2]
