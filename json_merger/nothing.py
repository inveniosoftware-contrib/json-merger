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


class Nothing(object):

    def __eq__(self, other):
        if isinstance(other, Nothing):
            return True
        return False

    def __ne__(self, other):
        if isinstance(other, Nothing):
            return False
        return True

    def __nonzero__(self):
        return False

    def __bool__(self):
        return False

    def __str__(self):
        return 'NOTHING'

    def __repr__(self):
        return 'NOTHING'


# Create a new placeholder for None objects that doesn't conflict with None
# entries in the dicts.
NOTHING = Nothing()
