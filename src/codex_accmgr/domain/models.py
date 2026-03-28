from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SavedAccount:
    alias: str
    email: str
    plan: str


@dataclass(frozen=True)
class CurrentAccountInfo:
    alias: str
    email: str
    plan: str


@dataclass(frozen=True)
class SwitchResult:
    alias: str
    email: str
    plan: str
    refresh_message: str
    persistence_warning: str | None = None


@dataclass(frozen=True)
class ClearAuthResult:
    refresh_message: str
