from __future__ import annotations

from .application.services import AccountApplicationService
from .infrastructure.accounts import AccountStorage
from .infrastructure.desktop import DesktopRefresher
from .infrastructure.paths import AppPaths
from .infrastructure.shell import ShellProfileInstaller
from .infrastructure.usage import SessionUsageReader


def build_account_service() -> AccountApplicationService:
    paths = AppPaths.default()
    return AccountApplicationService(
        storage=AccountStorage(paths),
        usage_reader=SessionUsageReader(paths.sessions_dir),
        desktop=DesktopRefresher(paths),
        installer=ShellProfileInstaller(paths.project_root),
    )
