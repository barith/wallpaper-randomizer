"""Unit tests for ``wallpaper_randomizer.wallpaper_setter.WallpaperSetter``.

Everything external is neutralized so the suite runs offline, deterministically
and identically on macOS, Linux and Windows:

* ``platform.system`` is patched on the ``wallpaper_setter`` module's own
  reference, so the OS branch taken by ``__init__`` / ``set_wallpaper`` is
  fully controlled (no real wallpaper is ever set).
* Desktop-environment detection is driven either by explicitly set/unset
  environment variables, or by a faked ``subprocess.check_output`` returning
  a crafted ``ps`` listing.
* The private ``_set_*_wallpaper`` methods are replaced with call-recording
  stubs. The two command-construction tests monkeypatch ``subprocess.run`` to
  capture argv; no real ``osascript`` / ``ctypes`` / ``gsettings`` / ``feh`` /
  ``swaybg`` process is ever spawned.
"""

import subprocess
from pathlib import Path

import pytest

import wallpaper_randomizer.wallpaper_setter as wallpaper_setter
from wallpaper_randomizer.wallpaper_setter import WallpaperSetter

from .helpers import make_png

#: Every environment variable consulted by ``_detect_desktop_environment``.
_DETECTION_ENV_VARS = (
    'XDG_CURRENT_DESKTOP',
    'DESKTOP_SESSION',
    'WAYLAND_DISPLAY',
    'SWAYSOCK',
    'HYPRLAND_INSTANCE_SIGNATURE',
)

#: The per-OS / per-DE wallpaper methods that ``set_wallpaper`` may dispatch to.
LEAF_METHODS = (
    '_set_macos_wallpaper',
    '_set_windows_wallpaper',
    '_set_i3_wallpaper',
    '_set_sway_wallpaper',
    '_set_hyprland_wallpaper',
    '_set_gnome_wallpaper',
    '_set_kde_wallpaper',
    '_set_xfce_wallpaper',
    '_set_mate_wallpaper',
    '_set_cinnamon_wallpaper',
)


def _no_ps(*args, **kwargs):
    """Stand-in for ``check_output``: pretend the ``ps`` fallback is unusable."""
    raise FileNotFoundError("ps is unavailable in the test environment")


def _record_stub(method_name, calls=None, result=True, exc=None):
    """Build a stub for a private ``_set_*_wallpaper`` method.

    Records ``(method_name, image_path)`` into *calls* (when given), raises
    *exc* (when given) and otherwise returns *result*.
    """

    def _stub(image_path):
        if calls is not None:
            calls.append((method_name, image_path))
        if exc is not None:
            raise exc
        return result

    return _stub


def _install_leaf_stubs(setter, monkeypatch, calls):
    """Replace every leaf ``_set_*_wallpaper`` method on *setter* with a stub."""
    for name in LEAF_METHODS:
        monkeypatch.setattr(setter, name, _record_stub(name, calls))


@pytest.fixture
def linux_env(monkeypatch):
    """Force the module to see a Linux host with a clean detection environment.

    Patches ``platform.system`` on the ``wallpaper_setter`` module so that
    ``WallpaperSetter.__init__`` runs desktop-environment detection on *any*
    host, and unsets every env var the detector consults so each test starts
    from a known state. ``monkeypatch`` restores everything automatically.
    """
    monkeypatch.setattr(wallpaper_setter.platform, 'system', lambda: 'Linux')
    for name in _DETECTION_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def setter(monkeypatch):
    """A ``WallpaperSetter`` with detection neutralized.

    ``platform.system`` is forced to ``'Linux'``, all detection env vars are
    unset and the ``ps`` fallback is made to fail, so the instance always
    starts as ``(system='Linux', desktop_env=None)`` regardless of which host
    runs the tests. Routing tests then override ``system`` / ``desktop_env``.
    """
    monkeypatch.setattr(wallpaper_setter.platform, 'system', lambda: 'Linux')
    for name in _DETECTION_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(wallpaper_setter.subprocess, 'check_output', _no_ps)
    return WallpaperSetter()


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('system', ['Darwin', 'Windows'])
def test_init_off_linux_skips_desktop_detection(monkeypatch, system):
    monkeypatch.setattr(wallpaper_setter.platform, 'system', lambda: system)
    ws = WallpaperSetter()
    assert ws.system == system
    assert ws.desktop_env is None


def test_init_on_linux_runs_detection(monkeypatch):
    monkeypatch.setattr(wallpaper_setter.platform, 'system', lambda: 'Linux')
    for name in _DETECTION_ENV_VARS:
        monkeypatch.delenv(name, raising=False)

    def fake_check_output(args, **kwargs):
        assert args == ['ps', '-A']
        return 'USER   PID\nroot      1  /usr/libexec/gnome-shell\n'

    monkeypatch.setattr(wallpaper_setter.subprocess, 'check_output',
                        fake_check_output)

    ws = WallpaperSetter()
    assert ws.system == 'Linux'
    assert ws.desktop_env == 'gnome'


# ---------------------------------------------------------------------------
# _detect_desktop_environment: environment variables
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('env, expected', [
    # sway (Wayland compositor)
    ({'XDG_CURRENT_DESKTOP': 'sway'}, 'sway'),
    ({'DESKTOP_SESSION': 'sway'}, 'sway'),
    ({'SWAYSOCK': '/run/user/1000/sway-sock'}, 'sway'),
    # hyprland (Wayland compositor)
    ({'XDG_CURRENT_DESKTOP': 'Hyprland'}, 'hyprland'),  # case-insensitive
    ({'HYPRLAND_INSTANCE_SIGNATURE': 'sig-abc123'}, 'hyprland'),
    # i3 (X11 window manager; no sway/hyprland indicators present)
    ({'XDG_CURRENT_DESKTOP': 'i3'}, 'i3'),
    # traditional desktop environments
    ({'XDG_CURRENT_DESKTOP': 'GNOME'}, 'gnome'),
    ({'XDG_CURRENT_DESKTOP': 'ubuntu'}, 'gnome'),
    ({'XDG_CURRENT_DESKTOP': 'KDE'}, 'kde'),
    ({'XDG_CURRENT_DESKTOP': 'plasma'}, 'kde'),
    ({'XDG_CURRENT_DESKTOP': 'XFCE'}, 'xfce'),
    ({'XDG_CURRENT_DESKTOP': 'MATE'}, 'mate'),
    ({'XDG_CURRENT_DESKTOP': 'Cinnamon'}, 'cinnamon'),
])
def test_detect_desktop_environment_from_env_vars(linux_env, monkeypatch,
                                                  env, expected):
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    ws = WallpaperSetter()
    assert ws.desktop_env == expected


# ---------------------------------------------------------------------------
# _detect_desktop_environment: ``ps`` fallback
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('listing, extra_env, expected', [
    # sway / hyprland are only recognized from the process list when a
    # Wayland display is in the environment.
    ('USER   PID\nalice    42  /usr/bin/sway\n',
     {'WAYLAND_DISPLAY': 'wayland-1'}, 'sway'),
    ('USER   PID\nbob     137  /usr/bin/Hyprland\n',
     {'WAYLAND_DISPLAY': 'hypr-1'}, 'hyprland'),
    # ...but not without one.
    ('USER   PID\nalice    42  /usr/bin/sway\n', {}, None),
    # X11 / traditional desktops do not need a Wayland display.
    ('USER   PID\nroot      1  /usr/libexec/gnome-shell\n', {}, 'gnome'),
    ('USER   PID\ncarol   101  /usr/bin/plasmashell\n', {}, 'kde'),
    ('USER   PID\ndave    150  /usr/bin/kwin_x11\n', {}, 'kde'),
    ('USER   PID\nerin    200  /usr/bin/i3\n', {}, 'i3'),
    ('USER   PID\nfrank   250  /usr/bin/xfce4-session\n', {}, 'xfce'),
    # Unrelated or empty listings yield no detection.
    ('USER   PID\nroot      1  /sbin/init\nroot     12  /usr/sbin/sshd\n',
     {}, None),
    ('', {}, None),
])
def test_detect_desktop_environment_ps_fallback(linux_env, monkeypatch,
                                                listing, extra_env, expected):
    for key, value in extra_env.items():
        monkeypatch.setenv(key, value)

    def fake_check_output(args, **kwargs):
        assert args == ['ps', '-A']
        return listing

    monkeypatch.setattr(wallpaper_setter.subprocess, 'check_output',
                        fake_check_output)

    ws = WallpaperSetter()
    assert ws.desktop_env == expected


def test_detect_desktop_environment_check_output_failure_returns_none(
        linux_env, monkeypatch):
    def boom(*args, **kwargs):
        raise FileNotFoundError('no ps binary')

    monkeypatch.setattr(wallpaper_setter.subprocess, 'check_output', boom)

    ws = WallpaperSetter()
    assert ws.desktop_env is None


# ---------------------------------------------------------------------------
# set_wallpaper: routing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('system, desktop_env, expected_method', [
    ('Darwin', None, '_set_macos_wallpaper'),
    ('Windows', None, '_set_windows_wallpaper'),
    ('Linux', 'i3', '_set_i3_wallpaper'),
    ('Linux', 'sway', '_set_sway_wallpaper'),
    ('Linux', 'hyprland', '_set_hyprland_wallpaper'),
    ('Linux', 'gnome', '_set_gnome_wallpaper'),
    ('Linux', 'kde', '_set_kde_wallpaper'),
    ('Linux', 'xfce', '_set_xfce_wallpaper'),
    ('Linux', 'mate', '_set_mate_wallpaper'),
    ('Linux', 'cinnamon', '_set_cinnamon_wallpaper'),
    # Unknown / undetected desktop environment -> GNOME fallback.
    ('Linux', None, '_set_gnome_wallpaper'),
    ('Linux', 'some-unknown-de', '_set_gnome_wallpaper'),
    # Unsupported operating system -> no method at all.
    ('FreeBSD', None, None),
])
def test_set_wallpaper_dispatches_to_correct_method(setter, monkeypatch,
                                                    tmp_path, system,
                                                    desktop_env,
                                                    expected_method):
    wall = make_png(tmp_path / 'wall.png', 8, 8)
    calls = []
    _install_leaf_stubs(setter, monkeypatch, calls)

    setter.system = system
    setter.desktop_env = desktop_env
    result = setter.set_wallpaper(wall)

    if expected_method is None:
        assert result is False
        assert calls == []
    else:
        assert result is True
        assert calls == [(expected_method, wall.absolute())]


@pytest.mark.parametrize('system', ['Darwin', 'Windows', 'Linux'])
def test_set_wallpaper_missing_image_returns_false(setter, monkeypatch,
                                                   tmp_path, system):
    calls = []
    _install_leaf_stubs(setter, monkeypatch, calls)

    setter.system = system
    setter.desktop_env = 'gnome'
    missing = tmp_path / 'does-not-exist.png'

    assert setter.set_wallpaper(missing) is False
    assert calls == []


def test_set_wallpaper_returns_false_when_setter_fails(setter, monkeypatch,
                                                       tmp_path):
    wall = make_png(tmp_path / 'wall.png', 8, 8)
    monkeypatch.setattr(setter, '_set_macos_wallpaper',
                        _record_stub('_set_macos_wallpaper', result=False))
    setter.system = 'Darwin'

    assert setter.set_wallpaper(wall) is False


def test_set_wallpaper_catches_exception_from_setter(setter, monkeypatch,
                                                     tmp_path):
    wall = make_png(tmp_path / 'wall.png', 8, 8)
    monkeypatch.setattr(
        setter, '_set_macos_wallpaper',
        _record_stub('_set_macos_wallpaper', exc=RuntimeError('boom')))
    setter.system = 'Darwin'

    assert setter.set_wallpaper(wall) is False


def test_set_wallpaper_resolves_relative_path_to_absolute(setter, monkeypatch,
                                                          tmp_path):
    make_png(tmp_path / 'wall.png', 8, 8)
    monkeypatch.chdir(tmp_path)

    calls = []
    monkeypatch.setattr(setter, '_set_macos_wallpaper',
                        _record_stub('_set_macos_wallpaper', calls))
    setter.system = 'Darwin'

    assert setter.set_wallpaper(Path('wall.png')) is True

    method, received = calls[0]
    assert method == '_set_macos_wallpaper'
    assert isinstance(received, Path)
    assert received.is_absolute()
    assert received == Path.cwd() / 'wall.png'


# ---------------------------------------------------------------------------
# Command construction (argv capture, nothing is executed for real)
# ---------------------------------------------------------------------------

def test_set_gnome_wallpaper_runs_gsettings_for_uri_dark_and_zoom(
        setter, tmp_path, monkeypatch):
    wall = make_png(tmp_path / 'wall.png', 8, 8)
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(wallpaper_setter.subprocess, 'run', fake_run)

    assert setter._set_gnome_wallpaper(wall) is True

    uri = f'file://{wall}'
    assert calls == [
        ['gsettings', 'set', 'org.gnome.desktop.background',
         'picture-uri', uri],
        ['gsettings', 'set', 'org.gnome.desktop.background',
         'picture-uri-dark', uri],
        ['gsettings', 'set', 'org.gnome.desktop.background',
         'picture-options', 'zoom'],
    ]


def test_set_gnome_wallpaper_returns_false_when_gsettings_fails(
        setter, tmp_path, monkeypatch):
    wall = make_png(tmp_path / 'wall.png', 8, 8)

    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(args, 1, stderr='no gsettings')

    monkeypatch.setattr(wallpaper_setter.subprocess, 'run', fake_run)

    assert setter._set_gnome_wallpaper(wall) is False


def test_set_i3_wallpaper_prefers_feh(setter, tmp_path, monkeypatch):
    wall = make_png(tmp_path / 'wall.png', 8, 8)
    calls = []
    monkeypatch.setattr(setter, '_command_exists', lambda cmd: cmd == 'feh')

    def fake_run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(wallpaper_setter.subprocess, 'run', fake_run)

    assert setter._set_i3_wallpaper(wall) is True
    assert calls == [['feh', '--bg-fill', str(wall)]]


def test_set_i3_wallpaper_falls_back_to_nitrogen(setter, tmp_path, monkeypatch):
    wall = make_png(tmp_path / 'wall.png', 8, 8)
    calls = []
    monkeypatch.setattr(setter, '_command_exists', lambda cmd: cmd == 'nitrogen')

    def fake_run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(wallpaper_setter.subprocess, 'run', fake_run)

    assert setter._set_i3_wallpaper(wall) is True
    assert calls == [['nitrogen', '--set-zoom-fill', str(wall)]]


def test_set_i3_wallpaper_without_any_tool_returns_false(setter, tmp_path,
                                                        monkeypatch):
    wall = make_png(tmp_path / 'wall.png', 8, 8)
    calls = []
    monkeypatch.setattr(setter, '_command_exists', lambda cmd: False)

    def fake_run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(wallpaper_setter.subprocess, 'run', fake_run)

    assert setter._set_i3_wallpaper(wall) is False
    assert calls == []