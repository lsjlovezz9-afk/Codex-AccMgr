from __future__ import annotations

import argparse
import os
import sys

from ..bootstrap import build_account_service
from ..constants import APP_NAME, APP_VERSION, BANNER_WIDTH, SUBTITLE
from ..domain.auth import mask_email
from ..domain.errors import CodexAccMgrError


class CliApp:
    def __init__(self, service):
        self.service = service
        self.use_color = sys.stdout.isatty() and os.getenv("NO_COLOR") is None

    def run(self, prompt_install: bool = True) -> int:
        self._enable_ansi()
        if prompt_install and sys.stdin.isatty() and not self.service.is_shell_installed():
            print(
                f"{APP_NAME} is not installed in your shell profile. / "
                f"{APP_NAME} 未在您的 Shell 配置文件中安装。"
            )
            choice = self._read_input("Do you want to install it now? (y/n) / 是否现在安装？(y/n): ")
            if choice and choice.lower() == "y":
                print(self.service.install_shell_alias())
                return 0

        while True:
            current_info = self.service.get_current_account_info()
            usage = self.service.get_usage_summary()

            print("")
            self._banner()
            print(f"\n{'=' * 50}")
            print("Current Account / 当前账号:")
            print(" Alias / 别名 |  Email / 邮箱            |  Plan / 订阅 | Usage / 额度")
            print(
                f" {current_info.alias:<12} |  "
                f"{mask_email(current_info.email):<23} |  "
                f"{current_info.plan:<12}| "
                f"{usage}"
            )
            print(f"{'=' * 50}")
            print("")
            print("[1] 查看账号 / List Accounts")
            print("[2] 添加账号 / Add Account")
            print("[3] 删除账号 / Remove Account")
            print("[4] 切换账号 / Switch Account")
            print("[q] 退出程序 / Exit")
            print("")

            choice = self._read_input("Select an option / 请选择操作: ")
            if choice is None:
                print("Goodbye / 再见")
                return 0
            choice = choice.lower()
            try:
                if choice == "1":
                    self._show_accounts(current_info.email)
                elif choice == "2":
                    self._add_account()
                elif choice == "3":
                    self._remove_account()
                elif choice == "4":
                    self._switch_account()
                elif choice == "q":
                    print("Goodbye / 再见")
                    return 0
                else:
                    print("Invalid choice / 无效选择")
            except CodexAccMgrError as error:
                print(str(error))

    def _show_accounts(self, current_email: str) -> None:
        accounts = self.service.list_accounts()
        if not accounts:
            print("No accounts found / 未找到账号")
            return
        self._section("Account List")
        print(f"\n{'=' * 60}")
        print(f"{'Alias/别名':<15} {'Email/邮箱':<30} {'Plan/订阅':<10}")
        print(f"{'-' * 60}")
        for account in accounts:
            marker = ""
            if current_email != "N/A" and account.email.lower() == current_email.lower():
                marker = " *"
            print(f"{account.alias:<15} {account.email:<30} {account.plan:<10}{marker}")
        print(f"{'=' * 60}")
        print("* = Current account / * = 当前账号")

    def _add_account(self) -> None:
        alias = self._read_input("Enter alias for new account (q to cancel) / 输入新账号别名(q 取消): ")
        if alias is None or alias.lower() == "q":
            print("Canceled. / 已取消。")
            return
        if not alias:
            print("Alias cannot be empty / 别名不能为空")
            return
        account = self.service.add_current_account(alias)
        print(f"Account '{account.alias}' created. / 账号 '{account.alias}' 已创建。")
        print(f"  Email: {account.email}")
        print(f"  Plan: {account.plan}")

    def _remove_account(self) -> None:
        accounts = self.service.list_accounts()
        if not accounts:
            print("No accounts found / 未找到账号")
            return

        self._section("Remove Account")
        print("\nSelect account to remove / 选择要删除的账号:")
        for index, account in enumerate(accounts, start=1):
            print(f"  {index}. {account.alias} ({account.email} - {account.plan})")
        print("  q. Cancel / 取消")

        choice = self._read_input("Select index / 选择序号: ")
        if choice is None or choice.lower() == "q":
            print("Canceled. / 已取消。")
            return
        if not choice.isdigit() or not (1 <= int(choice) <= len(accounts)):
            print("Invalid choice / 无效选择")
            return

        account = self.service.remove_account(accounts[int(choice) - 1].alias)
        print(f"Account '{account.alias}' removed. / 账号 '{account.alias}' 已删除。")

    def _switch_account(self) -> None:
        accounts = self.service.list_accounts()

        self._section("Switch Account")
        print("\nSelect account to switch / 选择要切换的账号:")
        print("  0. Default (Clean) / 默认 (干净环境)")
        for index, account in enumerate(accounts, start=1):
            print(f"  {index}. {account.alias} ({account.email} - {account.plan})")
        print("  q. Cancel / 取消")

        choice = self._read_input("Select index / 选择序号: ")
        if choice is None:
            print("Canceled. / 已取消。")
            return
        if choice == "0":
            result = self.service.clear_current_auth()
            print("Switched to Default (Clean) environment. / 已切换到默认 (干净) 环境。")
            print(result.refresh_message)
            print("You can now login with a new account. / 您现在可以登录新账号。")
            return
        if choice.lower() == "q":
            print("Canceled. / 已取消。")
            return
        if not choice.isdigit() or not (1 <= int(choice) <= len(accounts)):
            print("Invalid choice / 无效选择")
            return

        result = self.service.switch_account(accounts[int(choice) - 1].alias)
        print(f"Successfully switched to account: {result.alias} / 已成功切换至账号: {result.alias}")
        print(f"  Email: {result.email}")
        print(f"  Plan: {result.plan}")
        print(result.refresh_message)
        if result.persistence_warning:
            print(result.persistence_warning)

    def _enable_ansi(self) -> None:
        if os.name == "nt":
            try:
                os.system("")
            except Exception:
                pass

    @staticmethod
    def _read_input(prompt: str) -> str | None:
        try:
            return input(prompt).strip()
        except EOFError:
            return None

    def _style(self, text: str, *codes: str) -> str:
        if not self.use_color or not codes:
            return text
        return "\033[" + ";".join(codes) + "m" + text + "\033[0m"

    def _banner(self) -> None:
        line = "+" + "-" * BANNER_WIDTH + "+"
        print(self._style(line, "36"))
        print(self._style(f"| {APP_NAME}{APP_VERSION:>{48 - len(APP_NAME)}} |", "36", "1"))
        print(self._style(f"| {SUBTITLE:<48} |", "36"))
        print(self._style(line, "36"))

    def _section(self, title: str) -> None:
        print(self._style(title, "36", "1"))
        print(self._style("-" * BANNER_WIDTH, "2"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-accmgr",
        description="Manage multiple Codex auth.json profiles from the CLI.",
    )
    parser.add_argument("--version", action="version", version=APP_VERSION)
    parser.add_argument("--gui", action="store_true", help="Launch the GUI entry point.")
    parser.add_argument(
        "--no-install-prompt",
        action="store_true",
        help="Skip the shell-profile installation prompt before entering the menu.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.gui:
        from ..gui import main as gui_main

        return gui_main([])
    return CliApp(build_account_service()).run(prompt_install=not args.no_install_prompt)
