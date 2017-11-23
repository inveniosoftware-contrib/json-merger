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


class DictMergerOps(object):
    """Possible strategies for merging two base values.

    Attributes:
        FALLBACK_KEEP_HEAD: In case of conflict keep the `head` value.

        FALLBACK_KEEP_UPDATE: In case of conflict keep the `update` value.
    """
    allowed_ops = [
        'FALLBACK_KEEP_HEAD',
        'FALLBACK_KEEP_UPDATE'
    ]

    @staticmethod
    def keep_longest(head, update, down_path):
        """Keep longest field among `head` and `update`.
        """
        return 'f' if len(head) >= len(update) else 's'


for mode in DictMergerOps.allowed_ops:
    setattr(DictMergerOps, mode, mode)


class UnifierOps(object):
    """
    Attributes:
        KEEP_ONLY_HEAD_ENTITIES: Merge entities in `update` with their match
            in `head` having as a base the match in `root`.

        KEEP_ONLY_UPDATE_ENTITIES: Merge entities in 'head' with their match
            in `update` having as a base the match in `root`.

        KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST: Perform an union of all
            entities from `head` and `update` and merge the matching ones.
            Also, preserve the order relations between the entities in both
            lists. If two entities can have the same position first pick the
            one that is present in the `head` object.

        KEEP_UPDATE_AND_HEAD_ENTITIES_UPDATE_FIRST: Same behavior as
            KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST but first pick the
            `update` entities.

        KEEP_UPDATE_ENTITIES_CONFLICT_ON_HEAD_DELETE: If an entity was added
            in the diff between the `root` and `head` lists but it's not
            present in the `update` list then raise a conflict.
    """
    allowed_ops = [
        'KEEP_ONLY_HEAD_ENTITIES',
        'KEEP_ONLY_UPDATE_ENTITIES',
        'KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST',
        'KEEP_UPDATE_AND_HEAD_ENTITIES_UPDATE_FIRST',
        'KEEP_UPDATE_ENTITIES_CONFLICT_ON_HEAD_DELETE',
    ]

for mode in UnifierOps.allowed_ops:
    setattr(UnifierOps, mode, mode)
