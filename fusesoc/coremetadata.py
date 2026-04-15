# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import importlib.resources
import json
import pathlib
from typing import Iterator, Union

import fastjsonschema

import fusesoc.utils


def _load_schema() -> dict:
    schema_text = (
        importlib.resources.files("fusesoc")
        .joinpath("schemas/coremetadata.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(schema_text)


class ProviderData:
    """Dict-like, attribute-accessible wrapper around a provider section."""

    def __init__(self, data: dict) -> None:
        object.__setattr__(self, "_data", data)

    def __getitem__(self, key: str):
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __getattr__(self, key: str):
        try:
            return self._data[key]
        except KeyError:
            raise AttributeError(
                f"'ProviderData' object has no attribute '{key}'"
            ) from None

    def keys(self) -> Iterator[str]:
        return self._data.keys()

    def __repr__(self) -> str:
        return f"ProviderData({self._data!r})"


class CoreMetadata:
    """
    Loader for a ``.core.metadata`` companion file.

    Usage::

        cm = CoreMetadata.from_file("servant.core.metadata")
        print(cm.provider.name)   # github
        print(cm["provider"].repo) # serv
    """

    def __init__(self, data: dict) -> None:
        self._data = data

    @classmethod
    def from_file(cls, path: Union[str, pathlib.Path]) -> "CoreMetadata":
        """Load and validate a metadata file, returning a CoreMetadata instance."""
        raw = fusesoc.utils.yaml_fread(pathlib.Path(path))

        schema = _load_schema()
        try:
            validator = fastjsonschema.compile(schema)
            validator(raw)
        except fastjsonschema.JsonSchemaDefinitionException as e:
            raise SyntaxError(f"Error parsing JSON Schema: {e}") from e
        except fastjsonschema.JsonSchemaException as e:
            raise SyntaxError(f"Error validating {e}") from e

        return cls(raw)

    def __getitem__(self, key: str):
        value = self._data[key]
        if key == "provider":
            return ProviderData(value)
        return value

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def keys(self) -> Iterator[str]:
        return self._data.keys()

    @property
    def provider(self) -> ProviderData:
        return ProviderData(self._data["provider"])

    def __repr__(self) -> str:
        return f"CoreMetadata({self._data!r})"
