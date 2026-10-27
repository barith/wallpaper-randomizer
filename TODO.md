# TODO / Follow-ups

Deferred items from the test-suite work (October 2026).

## Done
- [x] Automated test suite for core logic (175 tests; 100% coverage on
      `config`, `reddit_fetcher`, `image_handler`, `wallpaper_fetcher`)
- [x] GitHub Actions `Tests` workflow (unit job + secrets-gated live job)

## Optional / Later
- [ ] **Enable live integration test in CI** *(one-time setup, no code)*
      Add `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` as repository
      secrets. `tests/test_integration_live.py` is already in place and
      skips automatically until the secrets exist.
- [ ] **Trim the README testing note**
      Once the CI run is proven green a few times, the "Testing status"
      paragraph can shrink to a one-liner.
- [ ] **CLI coverage (`wallpaper_randomizer/__main__.py`)**
      Test the argparse wiring for `init` / `test-config` / `clear-cache` /
      `set` / `gui` with mocked components. Guard the test file with
      `pytest.importorskip("tkinter")` — `__main__` imports the GUI, so the
      file must skip on interpreters without Tk (it passes on CI runners,
      which ship Tk).
- [ ] **GUI tests under xvfb**
      Run `wallpaper_randomizer/gui.py` headless on CI (xvfb + Tk are
      available on ubuntu runners): window creation, config auto-save,
      preview rendering, button wiring. Bounded by what is reasonably
      automatable for a desktop app.
- [ ] **Deepen `wallpaper_setter` coverage (~51% today)**
      Capture/verify the exact argv for the remaining backends (kde, xfce,
      mate, cinnamon, sway, hyprland, macos, windows) via mocked
      `subprocess`/`ctypes` — detection and routing are already covered.
- [ ] **Optional: OS matrix for the test job**
      Extend `.github/workflows/tests.yml` to macos/windows if the GUI/CLI
      tests above are added. Not needed for the current pure-logic suite.
