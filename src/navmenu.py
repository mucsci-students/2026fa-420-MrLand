"""Backward-compatible entry point for the CLI view.

Used by: CLI."""

from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.views import navmenu as _navmenu

if __name__ == "__main__":
    _navmenu.main()
else:
    sys.modules[__name__] = _navmenu
