from __future__ import annotations

import time

from ..domain.errors import AccountNotFoundError
from ..domain.models import ClearAuthResult, CurrentAccountInfo, SavedAccount, SwitchResult


class AccountApplicationService:
    def __init__(self, storage, usage_reader, desktop, installer):
        self.storage = storage
        self.usage_reader = usage_reader
        self.desktop = desktop
        self.installer = installer

    def is_shell_installed(self) -> bool:
        return self.installer.is_installed()

    def install_shell_alias(self) -> str:
        return self.installer.install()

    def list_accounts(self) -> list[SavedAccount]:
        return sorted(self.storage.load_accounts().values(), key=lambda account: account.alias.lower())

    def get_usage_summary(self) -> str:
        return self.usage_reader.read_latest_usage()

    def get_current_account_info(self) -> CurrentAccountInfo:
        email, plan = self.storage.read_current_identity()
        if not email:
            return CurrentAccountInfo(
                alias="Not logged in / 未登录",
                email="N/A",
                plan="N/A",
            )

        for account in self.list_accounts():
            if account.email.lower() == email.lower():
                return CurrentAccountInfo(
                    alias=account.alias,
                    email=email,
                    plan=plan or account.plan or "Unknown",
                )

        alias = f"Unknown ({email.split('@', 1)[0]})"
        return CurrentAccountInfo(alias=alias, email=email, plan=plan or "Unknown")

    def add_current_account(self, alias: str) -> SavedAccount:
        return self.storage.store_current_account(alias)

    def remove_account(self, alias: str) -> SavedAccount:
        return self.storage.remove_saved_account(alias)

    def switch_account(self, alias_or_fragment: str) -> SwitchResult:
        account = self.storage.restore_saved_account(alias_or_fragment)
        refresh_message = self.desktop.refresh_after_auth_write(self.storage.auth_file)
        time.sleep(1.5)

        current_email, _ = self.storage.read_current_identity()
        warning = None
        if current_email and current_email.lower() != account.email.lower():
            warning = (
                "Detected auth.json was overwritten by desktop cache. "
                "Please close and reopen Codex desktop, then retry."
            )

        return SwitchResult(
            alias=account.alias,
            email=account.email,
            plan=account.plan,
            refresh_message=refresh_message,
            persistence_warning=warning,
        )

    def clear_current_auth(self) -> ClearAuthResult:
        self.storage.clear_current_auth()
        refresh_message = self.desktop.refresh_codex_app()
        return ClearAuthResult(refresh_message=refresh_message)

    def get_account(self, alias: str) -> SavedAccount:
        for account in self.list_accounts():
            if account.alias == alias:
                return account
        raise AccountNotFoundError(f"Account '{alias}' not found.")
