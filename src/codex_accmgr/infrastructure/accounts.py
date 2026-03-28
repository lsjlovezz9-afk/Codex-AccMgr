from __future__ import annotations

import json
import os
import shutil
import stat

from ..domain.auth import parse_jwt_email, parse_jwt_plan
from ..domain.errors import (
    AccountNotFoundError,
    AliasAlreadyExistsError,
    AuthStateInvalidError,
    AuthStateNotFoundError,
)
from ..domain.models import SavedAccount


class AccountStorage:
    def __init__(self, paths):
        self.paths = paths
        self.paths.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.paths.accounts_dir.mkdir(parents=True, exist_ok=True)
        if not self.paths.config_file.exists():
            self.paths.config_file.write_text("{}", encoding="utf-8")

    @property
    def auth_file(self):
        return self.paths.auth_file

    @staticmethod
    def _remove_readonly(func, path, _excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def load_accounts(self) -> dict[str, SavedAccount]:
        raw = json.loads(self.paths.config_file.read_text(encoding="utf-8"))
        accounts: dict[str, SavedAccount] = {}
        for alias, data in raw.items():
            accounts[alias] = SavedAccount(
                alias=alias,
                email=data.get("email", "Unknown"),
                plan=data.get("plan", "Unknown"),
            )
        return accounts

    def save_accounts(self, accounts: dict[str, SavedAccount]) -> None:
        payload = {
            alias: {
                "alias": account.alias,
                "email": account.email,
                "plan": account.plan,
            }
            for alias, account in accounts.items()
        }
        self.paths.config_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )

    def read_current_auth(self) -> dict | None:
        if not self.paths.auth_file.exists():
            return None
        try:
            return json.loads(self.paths.auth_file.read_text(encoding="utf-8"))
        except Exception:
            return None

    def read_current_identity(self) -> tuple[str | None, str | None]:
        auth_data = self.read_current_auth()
        if not auth_data:
            return None, None
        id_token = auth_data.get("tokens", {}).get("id_token", "")
        if not id_token:
            return None, None
        return parse_jwt_email(id_token), parse_jwt_plan(id_token)

    def store_current_account(self, alias: str) -> SavedAccount:
        accounts = self.load_accounts()
        if alias in accounts:
            raise AliasAlreadyExistsError(f"Alias '{alias}' already exists.")

        auth_data = self.read_current_auth()
        if not auth_data or not self.paths.auth_file.exists():
            raise AuthStateNotFoundError("No auth.json found. Please login first.")

        id_token = auth_data.get("tokens", {}).get("id_token", "")
        email = parse_jwt_email(id_token)
        plan = parse_jwt_plan(id_token)
        if not email:
            raise AuthStateInvalidError("Cannot parse email from auth.json.")

        account_dir = self.paths.accounts_dir / alias
        if account_dir.exists():
            shutil.rmtree(account_dir, onerror=self._remove_readonly)
        account_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.paths.auth_file, account_dir / "auth.json")

        account = SavedAccount(alias=alias, email=email, plan=plan)
        accounts[alias] = account
        self.save_accounts(accounts)
        return account

    def remove_saved_account(self, alias: str) -> SavedAccount:
        accounts = self.load_accounts()
        if alias not in accounts:
            raise AccountNotFoundError(f"Account '{alias}' not found.")

        account_dir = self.paths.accounts_dir / alias
        if account_dir.exists():
            shutil.rmtree(account_dir, onerror=self._remove_readonly)

        account = accounts.pop(alias)
        self.save_accounts(accounts)
        return account

    def _match_alias(self, alias_or_fragment: str) -> str | None:
        accounts = self.load_accounts()
        lowered = alias_or_fragment.lower()
        for alias in accounts:
            if alias.lower() == lowered:
                return alias
        for alias in accounts:
            if lowered in alias.lower():
                return alias
        return None

    def restore_saved_account(self, alias_or_fragment: str) -> SavedAccount:
        accounts = self.load_accounts()
        matched_alias = self._match_alias(alias_or_fragment)
        if not matched_alias:
            raise AccountNotFoundError(f"No account matched '{alias_or_fragment}'.")

        target_auth = self.paths.accounts_dir / matched_alias / "auth.json"
        if not target_auth.exists():
            raise AuthStateNotFoundError(f"No auth.json found for '{matched_alias}'.")

        self.paths.codex_home.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target_auth, self.paths.auth_file)
        try:
            os.utime(self.paths.auth_file, None)
        except Exception:
            pass
        return accounts[matched_alias]

    def clear_current_auth(self) -> None:
        if self.paths.auth_file.exists():
            self.paths.auth_file.unlink()
