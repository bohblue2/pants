# Copyright 2019 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

"""Autoformatter for Python.

See https://pants.readme.io/docs/python-linters-and-formatters and
https://black.readthedocs.io/en/stable/.
"""

from pants.backend.python.lint import python_fmt
from pants.backend.python.lint.black import rules as black_rules


def rules():
    return (*black_rules.rules(), *python_fmt.rules())
