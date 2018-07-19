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


"""Test inspirehep specific features."""

from __future__ import absolute_import, print_function

from json_merger.contrib.inspirehep.author_util import (NameInitial,
                                                        NameToken,
                                                        simple_tokenize)


def test_simple_tokenize_handles_unicode():
    name = u'Dœ, Jöhn Π.'

    result = simple_tokenize(name)
    expected = {
        'lastnames': [NameToken(u'dœ')],
        'nonlastnames': [NameToken(u'jöhn'), NameInitial(u'π')],
    }

    assert result == expected
