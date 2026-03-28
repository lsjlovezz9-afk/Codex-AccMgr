from __future__ import annotations

import argparse
import sys

from ..bootstrap import build_account_service
from ..constants import APP_NAME, APP_VERSION
from ..domain.auth import mask_email


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-accmgr-gui",
        description="Launch the Codex AccMgr GUI.",
    )
    parser.add_argument("--version", action="version", version=APP_VERSION)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)

    try:
        from PySide6.QtWidgets import (
            QApplication,
            QLabel,
            QListWidget,
            QPushButton,
            QVBoxLayout,
            QWidget,
        )
    except ImportError:
        print(
            "PySide6 is required for the GUI entry. Install it with "
            "`pip install .[gui]` or `pip install PySide6`.",
            file=sys.stderr,
        )
        return 1

    service = build_account_service()

    class MainWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(f"{APP_NAME} GUI")
            self.setMinimumWidth(520)

            self.current_label = QLabel()
            self.accounts_list = QListWidget()
            self.accounts_list.setAlternatingRowColors(True)
            hint_label = QLabel("Account mutations stay in the CLI entry for now.")
            refresh_button = QPushButton("Refresh")
            refresh_button.clicked.connect(self.refresh_view)

            layout = QVBoxLayout()
            layout.addWidget(self.current_label)
            layout.addWidget(self.accounts_list)
            layout.addWidget(hint_label)
            layout.addWidget(refresh_button)
            self.setLayout(layout)
            self.refresh_view()

        def refresh_view(self):
            current = service.get_current_account_info()
            usage = service.get_usage_summary()
            self.current_label.setText(
                f"Current: {current.alias}\n"
                f"Email: {mask_email(current.email)}\n"
                f"Plan: {current.plan}\n"
                f"Usage: {usage}"
            )
            self.accounts_list.clear()
            accounts = service.list_accounts()
            if not accounts:
                self.accounts_list.addItem("No saved accounts")
                return
            for account in accounts:
                self.accounts_list.addItem(
                    f"{account.alias} | {mask_email(account.email)} | {account.plan}"
                )

    app = QApplication([sys.argv[0], *(argv or [])])
    window = MainWindow()
    window.show()
    return app.exec()
