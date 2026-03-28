from __future__ import annotations

import os
import sys
from pathlib import Path

from ..constants import APP_ALIAS, APP_NAME


class ShellProfileInstaller:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def profile_path(self) -> Path:
        if os.name == "nt":
            profile_dir = Path.home() / "Documents" / "PowerShell"
            profile_dir.mkdir(parents=True, exist_ok=True)
            return profile_dir / "Microsoft.PowerShell_profile.ps1"
        return Path.home() / ".zshrc"

    def is_installed(self) -> bool:
        profile = self.profile_path()
        if not profile.exists():
            return False
        try:
            return APP_ALIAS in profile.read_text(encoding="utf-8")
        except Exception:
            return False

    def install(self) -> str:
        profile = self.profile_path()
        profile.parent.mkdir(parents=True, exist_ok=True)
        launcher_path = (self.project_root / "codex.py").resolve()
        python_path = Path(sys.executable).resolve()

        if os.name == "nt":
            snippet = f"\nfunction {APP_ALIAS} {{ & '{python_path}' '{launcher_path}' $args }}\n"
        else:
            snippet = f"\nalias {APP_ALIAS}='\"{python_path}\" \"{launcher_path}\"'\n"

        with open(profile, "a", encoding="utf-8") as handle:
            handle.write(snippet)

        return (
            f"{APP_NAME} installed! Please restart your terminal or run "
            f"'source {profile}'. / {APP_NAME} 安装成功！请重启终端或运行 'source {profile}'。"
        )
