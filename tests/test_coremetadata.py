# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import pathlib

import pytest

from fusesoc.coremetadata import CoreMetadata, ProviderData

METADATA_DIR = pathlib.Path(__file__).parent / "metadata"


def test_load_github_provider():
    cm = CoreMetadata.from_file(METADATA_DIR / "github.core.metadata")

    assert cm.provider.name == "github"
    assert cm.provider.user == "olofk"
    assert cm.provider.repo == "serv"
    assert cm.provider.version == "1.3.0"


def test_load_local_provider():
    cm = CoreMetadata.from_file(METADATA_DIR / "local.core.metadata")

    assert cm.provider.name == "local"


def test_load_git_provider():
    cm = CoreMetadata.from_file(METADATA_DIR / "git.core.metadata")

    assert cm.provider.name == "git"
    assert cm.provider.repo == "https://github.com/olofk/serv.git"
    assert cm.provider.version == "main"


def test_load_opencores_provider():
    cm = CoreMetadata.from_file(METADATA_DIR / "opencores.core.metadata")

    assert cm.provider.name == "opencores"
    assert cm.provider.repo_name == "uart16550"
    assert cm.provider.repo_root == "communication_controller/uart16550"
    assert cm.provider.revision == "1"


def test_load_svn_provider():
    cm = CoreMetadata.from_file(METADATA_DIR / "svn.core.metadata")

    assert cm.provider.name == "svn"
    assert cm.provider.url == "https://opencores.org/ocsvn/uart16550/uart16550/trunk"
    assert cm.provider.revision == "42"


def test_load_url_provider():
    cm = CoreMetadata.from_file(METADATA_DIR / "url.core.metadata")

    assert cm.provider.name == "url"
    assert cm.provider.url == "https://example.com/core.tar.gz"
    assert cm.provider.filetype == "tar"


def test_dict_accessors():
    cm = CoreMetadata.from_file(METADATA_DIR / "github.core.metadata")

    assert "provider" in cm
    assert list(cm.keys()) == ["provider"]

    provider = cm["provider"]
    assert isinstance(provider, ProviderData)
    assert provider["name"] == "github"
    assert "name" in provider
    assert "user" in provider
    assert set(provider.keys()) == {"name", "user", "repo", "version"}


def test_provider_attribute_error():
    cm = CoreMetadata.from_file(METADATA_DIR / "github.core.metadata")

    with pytest.raises(AttributeError):
        _ = cm.provider.nonexistent


def test_invalid_provider_name():
    with pytest.raises(SyntaxError):
        CoreMetadata.from_file(METADATA_DIR / "invalid_provider.core.metadata")


def test_missing_required_field():
    with pytest.raises(SyntaxError):
        CoreMetadata.from_file(METADATA_DIR / "missing_field.core.metadata")


def test_additional_properties():
    with pytest.raises(SyntaxError):
        CoreMetadata.from_file(METADATA_DIR / "extra_field.core.metadata")


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        CoreMetadata.from_file(METADATA_DIR / "nonexistent.core.metadata")
