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

from .nothing import NOTHING


def get_obj_at_key_path(obj, key_path, default=None):
    current = obj
    for k in key_path:
        try:
            current = current[k]
        except (KeyError, IndexError, TypeError):
            return default
    return current


def set_obj_at_key_path(obj, key_path, value):
    obj = get_obj_at_key_path(obj, key_path[:-1], NOTHING)
    if obj == NOTHING:
        raise KeyError(key_path)
    try:
        obj[key_path[-1]] = value
    except (KeyError, IndexError, TypeError):
        raise KeyError(key_path)


def del_obj_at_key_path(obj, key_path, raise_key_error=True):
    obj = get_obj_at_key_path(obj, key_path[:-1], NOTHING)
    not_found = True
    if obj != NOTHING:
        try:
            del obj[key_path[-1]]
        except (KeyError, IndexError, TypeError):
            if raise_key_error:
                raise KeyError(key_path)
