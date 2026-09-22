<!--
This file is part of Inspirehep.
Copyright (C) 2016 CERN.

Inspirehep is free software; you can redistribute it
and/or modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

Inspirehep is distributed in the hope that it will be
useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with Inspirehep; if not, write to the
Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
MA 02111-1307, USA.

In applying this license, CERN does not
waive the privileges and immunities granted to it by virtue of its status
as an Intergovernmental Organization or submit itself to any jurisdiction.
-->

# json-merger

[![Coverage Status](https://img.shields.io/coveralls/inspirehep/json-merger.svg)](https://coveralls.io/r/inspirehep/json-merger)
[![GitHub tag](https://img.shields.io/github/tag/inspirehep/json-merger.svg)](https://github.com/inspirehep/json-merger/releases)
[![PyPI downloads](https://img.shields.io/pypi/dm/json-merger.svg)](https://pypi.python.org/pypi/json-merger)
[![License](https://img.shields.io/github/license/inspirehep/json-merger.svg)](https://github.com/inspirehep/json-merger/blob/master/LICENSE)

Module for merging JSON Objects.

* Free software: GPLv2 license
* Documentation: https://pythonhosted.org/json-merger/

## Installation

This project uses [Poetry](https://python-poetry.org/) for dependency
management. Assuming you have Poetry installed, this is how you set up
your fork for local development:

```console
$ cd json-merger/
$ poetry install --with tests --extras contrib
```

You can now run the tests with:

```console
$ poetry run pytest
```
