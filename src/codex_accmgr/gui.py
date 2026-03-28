from __future__ import annotations

from .presentation.gui import main as gui_main


def main(argv: list[str] | None = None) -> int:
    return gui_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
