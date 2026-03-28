from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..constants import DEFAULT_CONFIG_PATH, PROJECT_ROOT


@dataclass(frozen=True)
class AppPaths:
    project_root: Path
    config_file: Path
    codex_home: Path
    auth_file: Path
    accounts_dir: Path
    sessions_dir: Path
    config_toml: Path

    @classmethod
    def default(cls) -> "AppPaths":
        codex_home = Path.home() / ".codex"
        return cls(
            project_root=PROJECT_ROOT,
            config_file=DEFAULT_CONFIG_PATH,
            codex_home=codex_home,
            auth_file=codex_home / "auth.json",
            accounts_dir=codex_home / "codex-accmgr",
            sessions_dir=codex_home / "sessions",
            config_toml=codex_home / "config.toml",
        )
