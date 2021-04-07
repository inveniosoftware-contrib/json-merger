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

import re

import editdistance
import six

from munkres import Munkres
from unidecode import unidecode

_RE_NAME_TOKEN_SEPARATOR = re.compile(r'[^\w\'-]+', re.UNICODE)


def _normalized_edit_dist(s1, s2):
    return float(editdistance.eval(s1, s2)) / max(len(s1), len(s2), 1)


class NameToken(object):
    def __init__(self, token):
        self.token = token.lower()

    def __eq__(self, other):
        return self.token == other.token

    def __repr__(self):
        return repr(u'{}: {}'.format(self.__class__.__name__,
                                     self.token))


class NameInitial(NameToken):
    def __eq__(self, other):
        return self.token == other.token[:len(self.token)]


def token_distance(t1, t2, initial_match_penalization):
    """Calculates the edit distance between two tokens."""
    if isinstance(t1, NameInitial) or isinstance(t2, NameInitial):
        if t1.token == t2.token:
            return 0
        if t1 == t2:
            return initial_match_penalization
        return 1.0
    return _normalized_edit_dist(t1.token, t2.token)


def simple_tokenize(name):
    """Simple tokenizer function to be used with the normalizers."""
    last_names, first_names = name.split(',')
    last_names = _RE_NAME_TOKEN_SEPARATOR.split(last_names)
    first_names = _RE_NAME_TOKEN_SEPARATOR.split(first_names)

    first_names = [NameToken(n) if len(n) > 1 else NameInitial(n)
                   for n in first_names if n]
    last_names = [NameToken(n) if len(n) > 1 else NameInitial(n)
                  for n in last_names if n]
    return {'lastnames': last_names,
            'nonlastnames': first_names}


class AuthorNameNormalizer(object):
    """Callable that normalizes an author name given a tokenizer function."""

    def __init__(self, tokenize_function,
                 first_names_number=None,
                 first_name_to_initial=False,
                 asciify=False):
        """Initialize the normalizer.

        Args:
            tokenize_function:
                A function that receives an author name and parses it out in
                the following format:
                    {'lastnames': NameToken instance list,
                     'nonlastnames': NameToken instance list}
            first_names_number:
                Max number of first names too keep in the normalized name.
                If None, keep all first names
            first_name_to_initial:
                If set to True, all first names will be transformed into
                initials.
            asciify:
                If set to True, all non-ASCII characters will be replaced by
                the closest ASCII character, e.g. 'é' -> 'e'.
        """

        self.tokenize_function = tokenize_function
        self.first_names_number = first_names_number
        self.first_name_to_initial = first_name_to_initial
        self.normalize_chars = lambda x: _asciify(x) if asciify else x

    def __call__(self, author):
        name = author.get('full_name', '')
        name = _decode_if_not_unicode(name)
        name = self.normalize_chars(name)
        tokens = self.tokenize_function(name)
        last_fn_char = 1 if self.first_name_to_initial else None
        last_fn_idx = self.first_names_number

        return (tuple(n.token.lower() for n in tokens['lastnames']) +
                tuple(n.token.lower()[:last_fn_char]
                      for n in tokens['nonlastnames'][:last_fn_idx]))


class AuthorNameDistanceCalculator(object):
    """Callable that calculates a distance between two author's names."""

    def __init__(self, tokenize_function, match_on_initial_penalization=0.05,
                 full_name_field='full_name'):
        """Initialize the distance calculator.

        Args:
            tokenize_function: A function that receives an author name and
                parses it out in the following format:
                  {'lastnames': NameToken instance list,
                   'nonlastnames': NameToken instance list}
            match_on_initial_penalization:
                The cost value of a match between an initial and a full name
                starting with the same letter.
            name_field:
                The field in which an author record keeps the full name.
        Note:
            The default match_on_initial_penalization had the best results
            on a test suite based on production data.
        """
        self.tokenize_function = tokenize_function
        self.match_on_initial_penalization = match_on_initial_penalization
        self.name_field = full_name_field

    def __call__(self, author1, author2):
        # Return 1.0 on missing features.
        if self.name_field not in author1:
            return 1.0
        if self.name_field not in author2:
            return 1.0

        # Normalize to unicode
        name_a1 = _asciify(_decode_if_not_unicode(author1[self.name_field]))
        name_a2 = _asciify(_decode_if_not_unicode(author2[self.name_field]))

        tokens_a1 = self.tokenize_function(name_a1)
        tokens_a2 = self.tokenize_function(name_a2)
        tokens_a1 = tokens_a1['lastnames'] + tokens_a1['nonlastnames']
        tokens_a2 = tokens_a2['lastnames'] + tokens_a2['nonlastnames']

        # Match all names by editdistance.
        dist_matrix = [
            [token_distance(t1, t2, self.match_on_initial_penalization)
             for t2 in tokens_a2] for t1 in tokens_a1]

        matcher = Munkres()
        indices = matcher.compute(dist_matrix)
        cost = 0.0
        matched_only_initials = True
        for idx_a1, idx_a2 in indices:
            cost += dist_matrix[idx_a1][idx_a2]
            if (not isinstance(tokens_a1[idx_a1], NameInitial) or
                    not isinstance(tokens_a2[idx_a2], NameInitial)):
                matched_only_initials = False

        # Johnny, D will not be equal with Donny, J
        if matched_only_initials:
            return 1.0

        return cost / max(min(len(tokens_a1), len(tokens_a2)), 1.0)


def _decode_if_not_unicode(value):
    to_return = value

    if not isinstance(value, six.text_type):
        to_return = value.decode('utf-8')

    return to_return


def _asciify(value):
    return six.text_type(unidecode(value))
