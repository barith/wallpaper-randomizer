"""Unit tests for ``wallpaper_randomizer.config.Config``.

Everything is offline and deterministic:

* Invalid / variant configs are built by mutating ``valid_config_dict()``
  and written to temp files with the ``write_config`` fixture.
* ``sys.frozen`` / ``sys.platform`` / env-var mutations all go through
  ``monkeypatch`` so state is restored automatically.
* Filesystem side effects are confined to ``tmp_path`` (and the repo root,
  only when it must be the CWD to find ``config.yaml.template``).
"""

import sys
from pathlib import Path

import pytest
import yaml

from wallpaper_randomizer.config import Config

from .helpers import valid_config_dict

REPO_ROOT = Path(__file__).resolve().parent.parent


def build_config(write_config, data: dict) -> Config:
    """Write ``data`` as YAML via the ``write_config`` fixture and load it."""
    return Config(write_config(data))


# ---------------------------------------------------------------------------
# _validate_config
# ---------------------------------------------------------------------------


class TestValidateConfig:
    def test_valid_config_passes(self, config):
        config._validate_config(config.data)  # must not raise

    @pytest.mark.parametrize(
        "section",
        ["subreddits", "min_resolution", "post_filter", "reddit", "cache_dir"],
    )
    def test_missing_required_section_raises(self, write_config, section):
        data = valid_config_dict()
        del data[section]
        with pytest.raises(ValueError, match=section):
            build_config(write_config, data)

    def test_empty_subreddits_list_raises(self, write_config):
        data = valid_config_dict()
        data["subreddits"] = []
        with pytest.raises(ValueError, match="non-empty list"):
            build_config(write_config, data)

    def test_non_list_subreddits_raises(self, write_config):
        data = valid_config_dict()
        data["subreddits"] = "wallpaper"
        with pytest.raises(ValueError, match="non-empty list"):
            build_config(write_config, data)

    @pytest.mark.parametrize(
        "width,height",
        [(0, 1080), (-1920, 1080), (1920, 0), (1920, -1080)],
    )
    def test_non_positive_resolution_raises(self, write_config, width, height):
        data = valid_config_dict()
        data["min_resolution"] = {"width": width, "height": height}
        with pytest.raises(ValueError, match="positive"):
            build_config(write_config, data)

    @pytest.mark.parametrize("missing_key", ["width", "height"])
    def test_resolution_missing_key_raises(self, write_config, missing_key):
        data = valid_config_dict()
        del data["min_resolution"][missing_key]
        with pytest.raises(ValueError, match="must contain"):
            build_config(write_config, data)

    def test_invalid_sort_raises(self, write_config):
        data = valid_config_dict()
        data["post_filter"]["sort"] = "not-a-sort"
        with pytest.raises(ValueError, match="'sort' must be one of"):
            build_config(write_config, data)

    @pytest.mark.parametrize("sort", ["top", "controversial"])
    def test_invalid_time_filter_for_top_or_controversial_raises(
        self, write_config, sort
    ):
        data = valid_config_dict()
        data["post_filter"]["sort"] = sort
        data["post_filter"]["time_filter"] = "decade"
        with pytest.raises(ValueError, match="'time_filter' must be one of"):
            build_config(write_config, data)

    def test_time_filter_not_checked_for_other_sorts(self, write_config):
        # A bogus time_filter is only invalid for top/controversial.
        data = valid_config_dict()
        data["post_filter"]["sort"] = "hot"
        data["post_filter"]["time_filter"] = "decade"
        cfg = build_config(write_config, data)
        assert cfg.data["post_filter"]["time_filter"] == "decade"

    def test_omitted_time_filter_defaults_to_valid_value(self, write_config):
        data = valid_config_dict()
        data["post_filter"]["sort"] = "top"
        del data["post_filter"]["time_filter"]
        cfg = build_config(write_config, data)  # default 'month' is valid
        assert cfg.data["post_filter"]["sort"] == "top"

    @pytest.mark.parametrize("client_id", ["YOUR_CLIENT_ID_HERE", ""])
    def test_unconfigured_client_id_raises(self, write_config, client_id):
        data = valid_config_dict()
        data["reddit"]["client_id"] = client_id
        with pytest.raises(ValueError, match="client_id"):
            build_config(write_config, data)

    @pytest.mark.parametrize("client_secret", ["YOUR_CLIENT_SECRET_HERE", ""])
    def test_unconfigured_client_secret_raises(self, write_config, client_secret):
        data = valid_config_dict()
        data["reddit"]["client_secret"] = client_secret
        with pytest.raises(ValueError, match="client_secret"):
            build_config(write_config, data)


# ---------------------------------------------------------------------------
# _load_config
# ---------------------------------------------------------------------------


class TestLoadConfig:
    def test_valid_file_loads_into_data(self, config):
        assert config.data == valid_config_dict()

    def test_missing_file_raises(self, tmp_path, monkeypatch):
        # chdir into an empty dir so ensure_config_exists() finds no
        # template and _load_config() raises FileNotFoundError instead.
        monkeypatch.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            Config(str(tmp_path / "does-not-exist.yaml"))


# ---------------------------------------------------------------------------
# Getters
# ---------------------------------------------------------------------------


class TestGetters:
    def test_get_subreddits_old_format_returned_as_is(self, config):
        assert config.get_subreddits() == ["wallpaper", "wallpapers"]

    def test_get_subreddits_new_format_returns_only_enabled(self, write_config):
        data = valid_config_dict()
        data["subreddits"] = [
            {"name": "wallpaper", "enabled": True},
            {"name": "wallpapers", "enabled": False},
            {"name": "linux", "enabled": True},
            {"name": "macos"},  # missing 'enabled' -> treated as enabled
        ]
        cfg = build_config(write_config, data)
        assert cfg.get_subreddits() == ["wallpaper", "linux", "macos"]

    def test_get_subreddits_with_state_old_format_converted(self, config):
        assert config.get_subreddits_with_state() == [
            {"name": "wallpaper", "enabled": True},
            {"name": "wallpapers", "enabled": True},
        ]

    def test_get_subreddits_with_state_new_format_passthrough(self, write_config):
        data = valid_config_dict()
        entries = [
            {"name": "wallpaper", "enabled": True},
            {"name": "wallpapers", "enabled": False},
        ]
        data["subreddits"] = entries
        cfg = build_config(write_config, data)
        assert cfg.get_subreddits_with_state() == entries

    def test_get_min_resolution(self, config):
        assert config.get_min_resolution() == (1920, 1080)

    def test_get_post_filter(self, config):
        assert config.get_post_filter() == valid_config_dict()["post_filter"]

    def test_get_reddit_credentials(self, config):
        assert config.get_reddit_credentials() == valid_config_dict()["reddit"]

    def test_get_max_cache_size_mb_defaults_to_500(self, write_config):
        data = valid_config_dict()
        del data["max_cache_size_mb"]
        assert build_config(write_config, data).get_max_cache_size_mb() == 500

    def test_get_max_cache_size_mb_explicit(self, write_config):
        data = valid_config_dict()
        data["max_cache_size_mb"] = 250
        assert build_config(write_config, data).get_max_cache_size_mb() == 250

    def test_get_wallpaper_tool_specified(self, write_config):
        data = valid_config_dict()
        data["wallpaper_tool"] = {"tool": "i3", "fill_mode": "scale"}
        assert build_config(write_config, data).get_wallpaper_tool() == "i3"

    def test_get_wallpaper_tool_dict_without_tool_key(self, write_config):
        data = valid_config_dict()
        data["wallpaper_tool"] = {"fill_mode": "scale"}
        assert build_config(write_config, data).get_wallpaper_tool() is None

    def test_get_wallpaper_tool_absent(self, config):
        assert config.get_wallpaper_tool() is None

    def test_get_wallpaper_tool_not_a_dict(self, write_config):
        data = valid_config_dict()
        data["wallpaper_tool"] = "i3"
        assert build_config(write_config, data).get_wallpaper_tool() is None

    def test_get_selection_mode_defaults_to_random(self, write_config):
        data = valid_config_dict()
        del data["post_filter"]["selection_mode"]
        assert build_config(write_config, data).get_selection_mode() == "random"

    def test_get_selection_mode_explicit(self, write_config):
        data = valid_config_dict()
        data["post_filter"]["selection_mode"] = "first"
        assert build_config(write_config, data).get_selection_mode() == "first"

    def test_get_retry_count_defaults_to_5(self, write_config):
        data = valid_config_dict()
        del data["post_filter"]["retry_count"]
        assert build_config(write_config, data).get_retry_count() == 5

    def test_get_retry_count_explicit(self, write_config):
        data = valid_config_dict()
        data["post_filter"]["retry_count"] = 7
        assert build_config(write_config, data).get_retry_count() == 7

    def test_get_filter_nsfw_defaults_to_true(self, write_config):
        data = valid_config_dict()
        del data["post_filter"]["filter_nsfw"]
        assert build_config(write_config, data).get_filter_nsfw() is True

    def test_get_filter_nsfw_explicit_false(self, write_config):
        data = valid_config_dict()
        data["post_filter"]["filter_nsfw"] = False
        assert build_config(write_config, data).get_filter_nsfw() is False

    def test_get_cache_dir(self, config):
        assert config.get_cache_dir() == Path("/tmp/wallpaper-randomizer-test-cache")


# ---------------------------------------------------------------------------
# ensure_config_exists (via __init__)
# ---------------------------------------------------------------------------


class TestEnsureConfigExists:
    def test_default_path_copies_template_when_config_missing(self, tmp_path, monkeypatch):
        # Use a *valid* template so the auto-created config passes validation.
        data = valid_config_dict()
        (tmp_path / "config.yaml.template").write_text(yaml.safe_dump(data))
        monkeypatch.chdir(tmp_path)
        cfg = Config()  # no path given -> default ./config.yaml
        assert cfg.config_path == "config.yaml"
        assert cfg.data == data
        assert (tmp_path / "config.yaml").read_text() == (
            tmp_path / "config.yaml.template"
        ).read_text()

    def test_frozen_uses_meipass_for_template(self, tmp_path, monkeypatch):
        data = valid_config_dict()
        (tmp_path / "config.yaml.template").write_text(yaml.safe_dump(data))
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
        cfg = Config(str(tmp_path / "created.yaml"))
        assert cfg.data == data
        assert (tmp_path / "created.yaml").read_text() == yaml.safe_dump(data)


# ---------------------------------------------------------------------------
# create_default_config
# ---------------------------------------------------------------------------


class TestCreateDefaultConfig:
    def test_creates_file_from_template(self, tmp_path, monkeypatch):
        # CWD must contain config.yaml.template -> repo root.
        monkeypatch.chdir(REPO_ROOT)
        target = tmp_path / "created-config.yaml"
        Config.create_default_config(str(target))
        assert target.exists()
        assert target.read_text() == (REPO_ROOT / "config.yaml.template").read_text()

    def test_refuses_to_overwrite_existing_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(REPO_ROOT)
        target = tmp_path / "existing.yaml"
        target.write_text("existing content")
        with pytest.raises(FileExistsError):
            Config.create_default_config(str(target))
        assert target.read_text() == "existing content"

    def test_missing_template_raises(self, tmp_path, monkeypatch):
        # Empty CWD: no config.yaml.template to copy from.
        monkeypatch.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            Config.create_default_config(str(tmp_path / "new.yaml"))
        assert not (tmp_path / "new.yaml").exists()


# ---------------------------------------------------------------------------
# get_default_config_path
# ---------------------------------------------------------------------------


class TestGetDefaultConfigPath:
    def test_dev_mode_returns_cwd_config(self, monkeypatch):
        monkeypatch.delattr(sys, "frozen", raising=False)
        assert Config.get_default_config_path() == Path("config.yaml")

    def test_frozen_win32_uses_appdata(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setenv("APPDATA", str(tmp_path / "AppData"))
        result = Config.get_default_config_path()
        expected = tmp_path / "AppData" / "WallpaperRandomizer" / "config.yaml"
        assert result == expected
        assert result.parent.is_dir()  # directory is created as a side effect

    def test_frozen_win32_falls_back_to_home_without_appdata(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "platform","win32")
        monkeypatch.delenv("APPDATA", raising=False)
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))
        result = Config.get_default_config_path()
        assert result == home / "AppData" / "Roaming" / "WallpaperRandomizer" / "config.yaml"

    def test_frozen_darwin_uses_application_support(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "platform","darwin")
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))
        result = Config.get_default_config_path()
        assert result == (
            home / "Library" / "Application Support" / "WallpaperRandomizer" / "config.yaml"
        )
        assert result.parent.is_dir()

    def test_frozen_linux_uses_xdg_config(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "platform","linux2")
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))
        result = Config.get_default_config_path()
        assert result == home / ".config" / "wallpaper-randomizer" / "config.yaml"
        assert result.parent.is_dir()