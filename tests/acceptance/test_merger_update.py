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

from json_merger import Merger
from json_merger.config import DictMergerOps, UnifierOps
from json_merger.errors import MergeError
from json_merger.contrib.inspirehep.comparators import (
        DistanceFunctionComparator)
from json_merger.contrib.inspirehep.author_util import (
        simple_tokenize, AuthorNameDistanceCalculator, AuthorNameNormalizer)
from json_merger.comparator import PrimaryKeyComparator

from json_merger.conflict import Conflict, ConflictType


class TitleComparator(PrimaryKeyComparator):

    primary_key_fields = ['source']


class AffiliationComparator(PrimaryKeyComparator):

    primary_key_fields = ['value']


class AuthorComparator(DistanceFunctionComparator):
    norm_functions = [
        # Better hints can be given by normalizing by primary key,
        # (e.g. recid, orcid, ...)
        # but this type of normalization is not implemented in contrib.
        AuthorNameNormalizer(simple_tokenize),
        AuthorNameNormalizer(simple_tokenize, 1),
        AuthorNameNormalizer(simple_tokenize, 1, True)
    ]
    distance_function = AuthorNameDistanceCalculator(simple_tokenize)
    threshold = 0.12


COMPARATORS = {
    'authors': AuthorComparator,
    'authors.affiliations': AffiliationComparator,
    'titles': TitleComparator
}

LIST_MERGE_OPS = {
    'titles': UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST,
    'authors.affiliations': UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST
}


def _deserialize_conflict(conflict_type, path, body):
    if conflict_type == ConflictType.MANUAL_MERGE:
        body = tuple(body)
    return Conflict(conflict_type, tuple(path), body)


@pytest.mark.parametrize('scenario', [
    'author_typo_update_fix',
    'author_typo_curator_fix',
    'author_typo_update_and_curator_fix',
    'author_typo_conflict',
    'author_prepend_and_curator_typo_fix',
    'author_delete_and_single_curator_typo_fix',
    'author_delete_and_double_curator_typo_fix',
    'author_reorder_and_double_curator_typo_fix',
    'author_reorder_conflict',
    'author_replace_and_single_curator_typo_fix',
    'author_delete_and_double_curator_typo_fix',
    'author_curator_collab_addition',
    'author_affiliation_addition',
    'author_double_match_conflict',
    'author_double_match_unambiguous_fix',
    'title_addition',
    'title_change'
])
def test_author_typo_scenarios(update_fixture_loader, scenario):
    root, head, update, exp, desc = update_fixture_loader.load_test(scenario)
    merger = Merger(root, head, update,
                    DictMergerOps.FALLBACK_KEEP_HEAD,
                    UnifierOps.KEEP_ONLY_UPDATE_ENTITIES,
                    comparators=COMPARATORS,
                    list_merge_ops=LIST_MERGE_OPS)
    if exp.get('conflicts'):
        with pytest.raises(MergeError) as excinfo:
            merger.merge()
        expected_conflicts = [_deserialize_conflict(t, p, b)
                              for t, p, b in exp.pop('conflicts')]
        assert set(expected_conflicts) == set(excinfo.value.content)
    else:
        merger.merge()

    assert merger.merged_root == exp, desc


def test_add_author_in_head(update_fixture_loader):

    root, head, update, exp, desc = update_fixture_loader.load_test(
        'author_added_only_in_head'
    )
    list_config = {
        'authors':
            UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_CONFLICT_ON_HEAD_DELETE
    }

    merger = Merger(root, head, update,
                    DictMergerOps.FALLBACK_KEEP_HEAD,
                    UnifierOps.KEEP_ONLY_UPDATE_ENTITIES,
                    comparators=COMPARATORS,
                    list_merge_ops=list_config)
    merger.merge()
    assert merger.merged_root == exp, desc


def test_author_deleted_in_update(update_fixture_loader):

    root, head, update, exp, desc = update_fixture_loader.load_test(
        'author_added_only_in_head'
    )
    list_config = {
        'authors':
            UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_CONFLICT_ON_HEAD_DELETE
    }

    merger = Merger(root, head, update,
                    DictMergerOps.FALLBACK_KEEP_HEAD,
                    UnifierOps.KEEP_ONLY_UPDATE_ENTITIES,
                    comparators=COMPARATORS,
                    list_merge_ops=list_config)
    merger.merge()
    assert merger.merged_root == exp, desc
