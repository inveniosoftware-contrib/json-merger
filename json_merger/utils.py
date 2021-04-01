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


def set_obj_at_key_path(obj, key_path, value, raise_key_error=True):
    try:
        return _set_obj_at_key_path(obj, key_path, value)
    except KeyError as e:
        if raise_key_error:
            raise e
        else:
            return obj


def _set_obj_at_key_path(obj, key_path, value):
    # We are setting the obj param to another value.
    if len(key_path) == 0:
        return value

    # Try to get the parent of the object to be set.
    parent = get_obj_at_key_path(obj, key_path[:-1], NOTHING)
    if parent == NOTHING:
        raise KeyError(key_path)
    try:
        parent[key_path[-1]] = value
    except (KeyError, IndexError, TypeError):
        raise KeyError(key_path)
    return obj


def del_obj_at_key_path(obj, key_path, raise_key_error=True):
    obj = get_obj_at_key_path(obj, key_path[:-1], NOTHING)
    if obj != NOTHING:
        try:
            del obj[key_path[-1]]
        except (KeyError, IndexError, TypeError):
            if raise_key_error:
                raise KeyError(key_path)
    elif raise_key_error:
        raise KeyError(key_path)


def has_prefix(key_path, prefix):
    return len(prefix) <= len(key_path) and key_path[:len(prefix)] == prefix


def remove_prefix(key_path, prefix):
    if not has_prefix(key_path, prefix):
        raise ValueError('Bad Prefix {}'.format(prefix))
    return key_path[len(prefix):]


def get_dotted_key_path(key_path, filter_int_keys=False):
    return '.'.join(k for k in key_path
                    if not isinstance(k, int) and filter_int_keys)


def get_conf_set_for_key_path(conf_set, key_path):
    prefix = get_dotted_key_path(key_path, True)
    return set(remove_prefix(k, prefix).lstrip('.')
               for k in conf_set if has_prefix(k, prefix))


def force_list(data):
    if not isinstance(data, (list, tuple, set)):
        return [data]
    elif isinstance(data, (tuple, set)):
        return list(data)
    return data


def dedupe_list(list_):
    """Remove duplicates from a list preserving the order.

    We might be tempted to use the list(set(l)) idiom, but it doesn't preserve
    the order, which hinders testability and does not work for lists with
    unhashable elements.
    """
    result = []

    for el in list_:
        if el not in result:
            result.append(el)

    return result
