# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

import os
from pathlib import Path, PurePath
from typing import Union

from pants.base.specs import (
    AddressSpec,
    DescendantAddresses,
    FilesystemGlobSpec,
    FilesystemIgnoreSpec,
    FilesystemLiteralSpec,
    FilesystemSpec,
    SiblingAddresses,
    SingleAddress,
)


class CmdLineSpecParser:
    """Parses address selectors and filesystem specs as passed from the command line.

    See the `specs` package for more information on the types of objects returned.
    This class supports some flexibility in the path portion of the spec to allow for more natural
    command line use cases like tab completion leaving a trailing / for directories and relative
    paths, ie both of these::

      ./src/::
      /absolute/path/to/project/src/::

    Are valid command line specs even though they are not a valid BUILD file specs.  They're both
    normalized to::

      src::

    The above expression would choose every target under src.
    """

    class BadSpecError(Exception):
        """Indicates an unparseable command line address selector."""

    def __init__(self, root_dir: str) -> None:
        self._root_dir = os.path.realpath(root_dir)

    def _normalize_spec_path(self, path: str) -> str:
        is_abs = not path.startswith("//") and os.path.isabs(path)
        if is_abs:
            path = os.path.realpath(path)
            if os.path.commonprefix([self._root_dir, path]) != self._root_dir:
                raise self.BadSpecError(
                    f"Absolute spec path {path} does not share build root {self._root_dir}"
                )
        else:
            if path.startswith("//"):
                path = path[2:]
            path = os.path.join(self._root_dir, path)

        normalized = os.path.relpath(path, self._root_dir)
        if normalized == ".":
            normalized = ""
        return normalized

    def parse_spec(self, spec: str) -> Union[AddressSpec, FilesystemSpec]:
        """Parse the given spec into an `AddressSpec` or `FilesystemSpec` object.

        :raises: CmdLineSpecParser.BadSpecError if the address selector could not be parsed.
        """
        if spec.endswith("::"):
            spec_path = spec[: -len("::")]
            return DescendantAddresses(directory=self._normalize_spec_path(spec_path))
        if spec.endswith(":"):
            spec_path = spec[: -len(":")]
            return SiblingAddresses(directory=self._normalize_spec_path(spec_path))
        if ":" in spec:
            spec_parts = spec.rsplit(":", 1)
            spec_path = self._normalize_spec_path(spec_parts[0])
            return SingleAddress(directory=spec_path, name=spec_parts[1])
        if spec.startswith("!"):
            return FilesystemIgnoreSpec(spec[1:])
        if "*" in spec:
            return FilesystemGlobSpec(spec)
        if PurePath(spec).suffix:
            return FilesystemLiteralSpec(self._normalize_spec_path(spec))
        spec_path = self._normalize_spec_path(spec)
        if Path(self._root_dir, spec_path).is_file():
            return FilesystemLiteralSpec(spec_path)
        # Else we apply address shorthand, i.e. `src/python/pants/util` -> `src/python/pants/util:util`
        # TODO: Figure out what this should look like if (once?) filesystem specs allow directories.
        # Should this shorthand be removed so that directories may be unambiguously resolved to a
        # FilesystemSpec? If so, do we still allow the shorthand in BUILD files?
        return SingleAddress(directory=spec_path, name=PurePath(spec).name)
