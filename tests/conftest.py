"""Shared pytest fixtures for the wallpaper_randomizer test suite.

Run tests from the repository root, e.g.::

    .venv/bin/python -m pytest tests/
    .venv/bin/python -m pytest tests/test_config.py

Fixtures provided here (available by name in any test module under ``tests/``):

    write_config       factory: write a config dict as YAML -> returns path str
    valid_config_file  path to a temp config.yaml that passes all Config validation
    config             a loaded ``wallpaper_randomizer.config.Config`` (valid temp file)
    cache_dir          a fresh temp directory to use as an image cache

Import the plain helpers from ``tests.helpers`` where you need to build inputs
inside a test body (see the docstring there).
"""

import sys
from pathlib import Path

import pytest
import yaml

# Ensure the repository root is importable no matter how pytest is invoked, so
# ``from wallpaper_randomizer...`` resolves in every test module.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def write_config(tmp_path):
    """Factory fixture: write a config dict as YAML and return the file path.

    Usage::

        path = write_config(my_config_dict)
    """

    def _write(data: dict, name: str = "config.yaml") -> str:
        p = tmp_path / name
        p.write_text(yaml.safe_dump(data))
        return str(p)

    return _write


@pytest.fixture
def valid_config_file(tmp_path, write_config):
    """Path to a temporary ``config.yaml`` that passes all Config validation."""
    from .helpers import valid_config_dict

    return write_config(valid_config_dict())


@pytest.fixture
def config(valid_config_file):
    """A fully loaded ``Config`` instance backed by a valid temp config file."""
    from wallpaper_randomizer.config import Config

    return Config(valid_config_file)


@pytest.fixture
def cache_dir(tmp_path):
    """A fresh temporary directory to use as an image cache."""
    d = tmp_path / "cache"
    d.mkdir()
    return d
