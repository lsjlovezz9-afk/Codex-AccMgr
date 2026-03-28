from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap_src_path() -> None:
    src_dir = Path(__file__).resolve().parent / "src"
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))


def main(argv: list[str] | None = None) -> int:
    _bootstrap_src_path()
    from codex_accmgr.__main__ import main as package_main

    return package_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
