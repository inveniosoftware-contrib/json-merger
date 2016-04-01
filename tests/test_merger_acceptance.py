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


"""Acceptance scenarios for the merger."""

from __future__ import absolute_import, print_function

import pytest

from json_merger import merge_records


@pytest.mark.xfail
@pytest.mark.parametrize('scenario', [
    'author_typo',
    'author_prepend',
    'author_delete',
    'author_prepend_and_typo',
    'author_delete_and_typo'])
def test_expected_outcome(json_loader, scenario):
    src, update, expected, desc = json_loader.load_test(scenario)
    assert merge_records(src, update) == expected, desc
