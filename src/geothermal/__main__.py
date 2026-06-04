"""Enable ``python -m geothermal …`` to run the command-line interface."""

from __future__ import annotations

from geothermal.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
