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

"""Module for merging JSON objects.

To use this module you need to first import the main class:

>>> from json_merger import Merger

Then, import the configuration options:

>>> from json_merger.config import UnifierOps, DictMergerOps

The Basic Use Case
------------------

Let's assume we have JSON records that don't have any list fields --
They have string keys and as values other objects or primitive types.
In order to perform a merge we assume we have a lowest common ancestor
(``root``), a current version (``head``) and another version wich we want to
integrate into our record (``update``).

>>> root = {'name': 'John'} # A common ancestor of our person record
>>> head = {'name': 'Johnny', 'age': 32} # The current version of the record.
>>> update = {'name': 'Jonathan', 'address': 'Home'} # An updated version.

In this case we want to use the merger to compute one of the possible versions.

We create a merger instance in which we provide the default operation for
non-list fields and the one for list fields.

>>> m = Merger(root, head, update, DictMergerOps.FALLBACK_KEEP_HEAD,
...            UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST)
...            # Ignore UnifierOps for now.
>>> # We might get some exceptions
>>> from json_merger.errors import MergeError
>>> try:
...     m.merge()
... except MergeError:
...     pass # We don't care about this now.
>>> m.merged_root == {
...     'name': 'Johnny',
...     'age': 32,
...     'address': 'Home',
... }
True

The merged version kept the ``age`` field from the ``head`` object and the
``address`` field from the ``update`` object. The ``name`` field was different,
but because the strategy was ``FALLBACK_KEEP_HEAD`` the end result kept the
value from the ``head`` variable. To keep the ``update`` one, one can
use ``FALLBACK_KEEP_UPDATE``:

>>> m = Merger(root, head, update, DictMergerOps.FALLBACK_KEEP_UPDATE,
...            UnifierOps.KEEP_ONLY_HEAD_ENTITIES)
>>> rasised_something = False
>>> try:
...     m.merge()
... except MergeError:
...     raised_something = True
>>> m.merged_root == {
...     'name': 'Jonathan',
...     'age': 32,
...     'address': 'Home',
... }
True

If this type of conflict occurs, the merger will also populate a ``conflicts``
field. In this case the conflict holds the alternative name for our record.
Also, because a conflict occurred, the merge method also raised a MergeError.

For all the types of conflict that can be raised by the ``merge`` method
also check the :class:`json_merger.conflict.ConflictType` documentation.

>>> from json_merger.conflict import Conflict, ConflictType
>>> m.conflicts[0] == Conflict(ConflictType.SET_FIELD, ('name', ), 'Johnny')
True
>>> raised_something
True

Merging Lists With Base Values
------------------------------

For this example we are going to assume we want to merge sets of badges
that a person can receive.

>>> root = {'badges': ['bad', 'random']}
>>> head = {'badges': ['cool', 'nice', 'random']}
>>> update = {'badges': ['fun', 'nice', 'healthy']}

The most simple options are to either keep only the badges available in head
or only the badges available in the update. This can be done by specifying one
of:

  * ``UnifierOps.KEEP_ONLY_HEAD_ENTITIES``
  * ``UnifierOps.KEEP_ONLY_UPDATE_ENTITIES``

>>> m = Merger(root, head, update, DictMergerOps.FALLBACK_KEEP_HEAD,
...            UnifierOps.KEEP_ONLY_HEAD_ENTITIES)
>>> m.merge() # No conflict here
>>> m.merged_root['badges'] == ['cool', 'nice', 'random']
True
>>> m = Merger(root, head, update, DictMergerOps.FALLBACK_KEEP_HEAD,
...            UnifierOps.KEEP_ONLY_UPDATE_ENTITIES)
>>> m.merge()
>>> m.merged_root['badges'] == ['fun', 'nice', 'healthy']
True

If we want to do a union of the elements we can use:

  * ``UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST``
  * ``UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_UPDATE_FIRST``

>>> m = Merger(root, head, update, DictMergerOps.FALLBACK_KEEP_HEAD,
...            UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST)
>>> m.merge() # No conflict here
>>> m.merged_root['badges'] == ['cool', 'fun', 'nice', 'random', 'healthy']
True
>>> m = Merger(root, head, update, DictMergerOps.FALLBACK_KEEP_HEAD,
...            UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_UPDATE_FIRST)
>>> m.merge()
>>> m.merged_root['badges'] == ['fun', 'cool', 'nice', 'healthy', 'random']
True

These options keep the order relations between the entities. For example,
both ``'fun'`` and ``'cool'`` were placed before the ``'nice'`` entity but
between them there isn't any restriction. In such cases, for
``KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST`` we first pick the elements
that occur only in the `head` list and for
``KEEP_UPDATE_AND_HEAD_ENTITIES_UPDATE_FIRST`` we first pick the ones that
occur only in the `update` list. If no such ordering is possible we first
add the elements found in the prioritized list and then the remaining ones.
Also, the method will raise a REORDER conflict.

>>> m = Merger([], [1, 2, 5, 3], [3, 1, 2, 4],
...            DictMergerOps.FALLBACK_KEEP_HEAD,
...            UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_HEAD_FIRST)
>>> try:
...     m.merge()
... except MergeError:
...     pass
>>> m.merged_root == [1, 2, 5, 3, 4]
True
>>> m.conflicts == [Conflict(ConflictType.REORDER, (), None)]
True
>>> m = Merger([], [1, 2, 5, 3], [3, 1, 2, 4],
...            DictMergerOps.FALLBACK_KEEP_HEAD,
...            UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_UPDATE_FIRST)
>>> try:
...     m.merge()
... except MergeError:
...     pass
>>> m.merged_root == [3, 1, 2, 4, 5]
True
>>> m.conflicts == [Conflict(ConflictType.REORDER, (), None)]
True

In the case in which ``root`` is represented by the latest automatic update
of a record (e.g. crawling some metadata source),
``head`` by manual edits of ``root`` and ``update`` by a new automatic
update, we might want to preserve only the entities in ``update`` but
notify the user in case some manual addition was removed.

  * ``UnifierOps.KEEP_UPDATE_ENTITIES_CONFLICT_ON_HEAD_DELETE``

>>> root = {'badges': ['bad', 'random']}
>>> head = {'badges': ['cool', 'nice', 'random']}
>>> update = {'badges': ['fun', 'nice', 'healthy']}
>>> m = Merger(root, head, update, DictMergerOps.FALLBACK_KEEP_HEAD,
...            UnifierOps.KEEP_UPDATE_ENTITIES_CONFLICT_ON_HEAD_DELETE)
>>> try:
...     m.merge()
... except MergeError:
...     pass
>>> m.merged_root['badges'] == ['fun', 'nice', 'healthy']
True
>>> m.conflicts == [Conflict(ConflictType.ADD_BACK_TO_HEAD,
...                          ('badges', ), 'cool')]
True

In this case, only ``'cool'`` was added "manually" and removed by the update.


Merging Lists Of Objects
------------------------

Assume the most complex case in which we need to merge lists of objects which
can also contain nested lists.

>>> root = {
...     'people': [
...         {'name': 'John', 'age': 13},
...         {'name': 'Peter'},
...         {'name': 'Max'}
...     ]}
>>> head = {
...     'people': [
...         {'name': 'John', 'age': 14,
...          'group': {'id': 'grp01'},
...          'person_id': '42',
...          'badges': [{'t': 'b0', 'e': True}, {'t': 'b1'}, {'t': 'b2'}]},
...         {'name': 'Peter', 'age': 15,
...          'badges': [{'t': 'b0'}, {'t': 'b1'}, {'t': 'b2'}]},
...         {'name': 'Max', 'age': 16}
...     ]}
>>> update = {
...     'people': [
...         {'name': 'Max', 'address': 'work'},
...         {'name': 'Johnnie', 'address': 'home',
...          'group': {'id': 'GRP01'},
...          'person_id': '42',
...          'age': 15,
...          'badges': [{'t': 'b1'}, {'t': 'b2'}, {'t': 'b0', 'e': False}]},
...     ]}

First of all we would like to define how to person records represent the same
entity. In this demo data model we can say that two records represent the
same person if any of the following is true:

  * They have the same ``name``
  * They have the same lowercased group id AND the same person_id

Then we define two badges as equal if they have the same ``t`` attribute.

In order to define a custom mode of linking records you can add comparator
classes for any of the list fields via the coparators keyword argument.
To define a simple comparsion that checks field equality you
can use :class:`json_merger.comparator.PrimaryKeyComparator`

In this case the fields from above look like this:

>>> from json_merger.comparator import PrimaryKeyComparator
>>> class PersonComparator(PrimaryKeyComparator):
...     primary_key_fields = ['name', ['group.id', 'person_id']]
...     normalization_functions = {'group.id': str.lower}
>>> class BadgesComparator(PrimaryKeyComparator):
...     primary_key_fields = ['t']

Note:
    You need to use a comparator class and not a comparator instance when
    defining the equality of two objects.

Next we would like to define how to do the merging:

  * In case of conflict keep ``head`` values.
  * For every list try to keep only the update entities.
  * For the badges list keep both entities with priority to the ``update``
    values.

>>> comparators = {'people': PersonComparator,
...                'people.badges': BadgesComparator}
>>> list_merge_ops = {
...     'people.badges': UnifierOps.KEEP_UPDATE_AND_HEAD_ENTITIES_UPDATE_FIRST
... }
>>> m = Merger(root, head, update,
...            DictMergerOps.FALLBACK_KEEP_HEAD,
...            UnifierOps.KEEP_ONLY_UPDATE_ENTITIES,
...            comparators=comparators,
...            list_merge_ops=list_merge_ops)
>>> try:
...     m.merge()
... except MergeError:
...     pass
>>> m.merged_root == {
...     'people': [
...         {'name': 'Max', 'address': 'work', 'age': 16},
...         {'name': 'Johnnie', # Only update edited it.
...          'address': 'home',
...          'group': {'id': 'grp01'}, # From KEEP_HEAD
...          'person_id': '42',
...          'age': 14, # From KEEP_HEAD
...          'badges': [{'t': 'b1'}, {'t': 'b2'},
...                     {'t': 'b0', 'e': True}], # From KEEP_HEAD
...         },
...     ]}
True

Merging Data Lists
------------------

If you want to merge arrays of raw data (that do not encode any entities),
you can use the ``data_lists`` keyword argument. This argument treats
list indices as dictionary keys.

>>> root = {'f': {'matrix': [[0, 0], [0, 0]]}}
>>> head = {'f': {'matrix': [[1, 1], [0, 0]]}}
>>> update = {'f': {'matrix': [[0, 0], [1, 1]]}}
>>> m = Merger(root, head, update,
...            DictMergerOps.FALLBACK_KEEP_HEAD,
...            UnifierOps.KEEP_ONLY_UPDATE_ENTITIES,
...            data_lists=['f.matrix'])
>>> m.merge()
>>> m.merged_root == {'f': {'matrix': [[1, 1], [1, 1]]}}
True

Extending Comparators
---------------------

The internal API uses classes that extend
:class:`json_merger.comparator.BaseComparator` in order to check the semantic
equality of JSON objects. The interals call the ``get_matches`` method which
is implemented in terms of the ``equals`` method.  The most simple method to
extend this class is to override the ``equals`` method.

>>> from json_merger.comparator import BaseComparator
>>> class CustomComparator(BaseComparator):
...     def equal(self, obj1, obj2):
...         return abs(obj1 - obj2) < 0.2
>>> comp = CustomComparator([1, 2], [1, 2, 1.1])
>>> comp.get_matches('l1', 0) # elements matching l1[0] from l2
[(0, 1), (2, 1.1)]

If you want to implement another type of asignment you an compute all the
mathes and store them in the ``matches`` set by overriding the
``process_lists`` method. You need to put pairs of matching indices between
l1 and l2.

>>> from json_merger.comparator import BaseComparator
>>> class CustomComparator(BaseComparator):
...     def process_lists(self):
...         self.matches.add((0, 0))
...         self.matches.add((0, 1))
>>> comp = CustomComparator(['foo', 'bar'], ['bar', 'foo'])
>>> comp.get_matches('l1', 0) # elements matching l1[0] from l2
[(0, 'bar'), (1, 'foo')]

[contrib] Distance Function Matching
------------------------------------

To implement fuzzy matching we also allow matching by using a distane
function. This ensures a 1:1 mapping betwen the entities by minimizing
the total distance between all linked entities. To mark two of them
as equal you can provide a threshold for that distance. (This is why
it's best to normalize it between 0 and 1). Also, for speeding
up the matching you also can hint possible matches by bucketing matching
elements using a normalization function. In the next example we would
match some points in the coordinate system, each of them lying in a specific
square. The distance that we are going to use is the euclidean distance.
We will normalize the points to their integer counterpart.

>>> from json_merger.contrib.inspirehep.comparators import (
...     DistanceFunctionComparator)
>>> from math import sqrt
>>> class PointComparator(DistanceFunctionComparator):
...     distance_function = lambda p1, p2: sqrt((p1[0] - p2[0]) ** 2 +
...                                             (p1[1] - p2[1]) ** 2)
...     normalization_functions = [lambda p: (int(p[0]), int(p[1]))]
...     threshold = 0.5
>>> l1 = [(1.1, 1.1), (1.2, 1.2), (2.1, 2.1)]
>>> l2 = [(1.11, 1.11), (1.25, 1.25), (2.15, 2.15)]
>>> comp = PointComparator(l1, l2)
>>> comp.get_matches('l1', 0) # elements matching l1[0] from l2
[(0, (1.11, 1.11))]
>>> # match only the closest element, not everything under threshold.
>>> comp.get_matches('l1', 1)
[(1, (1.25, 1.25))]
>>> comp.get_matches('l1', 2)
[(2, (2.15, 2.15))]

[contrib] Custom Person Name Distance
-------------------------------------

We also provide a person name distance based on edit distance normalized
between 0 and 1. You just need to provide a function for tokenizing a full
name into NameToken or NameInitial - check ``simple_tokenize`` in the
contrib directory. This distance function matches initials with full
regular tokens and works with any name permutation. Also, this distance
calculator assumes the full name is inside the ``full_name`` field of a
dictionary. If you have the name in a different field you can just override
the class and call ``super`` on objects having the name in the ``full_name``
field.

>>> from json_merger.contrib.inspirehep.author_util import (
...     AuthorNameDistanceCalculator, simple_tokenize)
>>> dst = AuthorNameDistanceCalculator(tokenize_function=simple_tokenize)
>>> dst({'full_name': u'Doe, J.'}, {'full_name': u'John, Doe'}) < 0.1
True

Also we have functions for normalizing an author name with different
heuristics to speed up the distance function matching.

>>> from json_merger.contrib.inspirehep.author_util import (
...     AuthorNameNormalizer)
>>> identity = AuthorNameNormalizer(simple_tokenize)
>>> identity({'full_name': 'Doe, Johnny Peter'})  # doctest: +SKIP
('doe', 'johnny', 'peter')
>>> asciified = AuthorNameNormalizer(simple_tokenize,
...                                  asciify=True)
>>> asciified({'full_name': 'Dœ, Jöhnny Péter'})  # doctest: +SKIP
('doe', 'johnny', 'peter')
>>> one_fst_name = AuthorNameNormalizer(simple_tokenize,
...                                     first_names_number=1)
>>> one_fst_name({'full_name': 'Doe, Johnny Peter'})  # doctest: +SKIP
('doe', 'johnny')
>>> last_name_one_initial = AuthorNameNormalizer(simple_tokenize,
...                                              first_names_number=1,
...                                              first_name_to_initial=True)
... # doctest: +SKIP
>>> last_name_one_initial({'full_name': 'Doe, Johnny Peter'})  # doctest: +SKIP
('doe', 'j')

These instances can be used as class parameters for
``DistanceFunctionComparator``
"""

from __future__ import absolute_import, print_function

from .merger import Merger
from .version import __version__

__all__ = ('__version__', 'Merger')
