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

import json
from pyrsistent import freeze, thaw


class ConflictType(object):
    """Types of Conflict.

    Attributes:
        REORDER: The list specified by the path might need to be reordered.

        MANUAL_MERGE: The triple specified as the conflict body needs to be
            manually merged and added to the conflict path.

        ADD_BACK_TO_HEAD: The object specified as the conflict body might
            need to be added back to the list specified in the conflict's path.

        SET_FIELD: The object specified as the conflict body needs to be
            added at the path specifed in the conflict object.

        REMOVE_FIELD: The value or object present at the path specified in
            the path conflict needs to be removed.
    """
    pass

_CONFLICTS = (
    'REORDER',
    'MANUAL_MERGE',
    'ADD_BACK_TO_HEAD',
    'SET_FIELD',
    'REMOVE_FIELD'
)
for conflict_type in _CONFLICTS:
    setattr(ConflictType, conflict_type, conflict_type)


class Conflict(tuple):
    """Immutable and Hashable representation of a conflict.

    Attributes:
        conflict_type: A :class:`json_merger.conflict.ConflictType` member.

        path: A tuple containing the path to the conflictual field.

        body: Optional value representing the body of the conflict.

    Note:
        Even if the conflict body can be any arbitrary object, this is saved
        internally as an immutable object so that a Conflict instance can be
        safely used in sets or as a dict key.
    """

    # Based on http://stackoverflow.com/a/4828108
    # Compatible with Python<=2.6

    def __new__(cls, conflict_type, path, body):
        if conflict_type not in _CONFLICTS:
            raise ValueError('Bad Conflict Type %s' % conflict_type)
        body = freeze(body)
        return tuple.__new__(cls, (conflict_type, path, body))

    conflict_type = property(lambda self: self[0])
    path = property(lambda self: self[1])
    body = property(lambda self: thaw(self[2]))

    def with_prefix(self, root_path):
        """Returns a new conflict with a prepended prefix as a path."""
        return Conflict(self.conflict_type, root_path + self.path, self.body)

    def to_json(self):
        """Deserializes conflict to a JSON object."""
        return json.dumps([self.conflict_type, self.path, self.body])
