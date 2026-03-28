from __future__ import annotations

import json
import os
from datetime import datetime


class SessionUsageReader:
    def __init__(self, sessions_dir):
        self.sessions_dir = sessions_dir

    def read_latest_usage(self) -> str:
        log_files: list[str] = []
        for root, _dirs, files in os.walk(self.sessions_dir):
            for name in files:
                if name.startswith("rollout-") and name.endswith(".jsonl"):
                    log_files.append(os.path.join(root, name))

        if not log_files:
            return "N/A"

        log_files.sort(key=os.path.getmtime, reverse=True)
        latest_file = log_files[0]
        try:
            with open(latest_file, "r", encoding="utf-8") as handle:
                lines = handle.readlines()
        except Exception:
            return "Error parsing logs / 日志解析错误"

        for line in reversed(lines):
            try:
                data = json.loads(line.strip())
            except Exception:
                continue
            if data.get("type") != "event_msg":
                continue
            payload = data.get("payload", {})
            if payload.get("type") != "token_count":
                continue
            return self._format_rate_limits(payload.get("rate_limits", {}))

        return "N/A"

    def _format_rate_limits(self, rate_limits: dict) -> str:
        limits = []
        primary = rate_limits.get("primary", {})
        secondary = rate_limits.get("secondary", {})
        if primary:
            limits.append(primary)
        if secondary:
            limits.append(secondary)
        if not limits:
            return "N/A"

        parts = []
        for limit in limits:
            used_percent = limit.get("used_percent", 0) or 0
            try:
                used_percent = float(used_percent)
            except Exception:
                used_percent = 0.0
            left_percent = round(max(0.0, 100.0 - used_percent), 1)
            parts.append(
                f"{self._label_for_window(limit.get('window_minutes'))}: "
                f"{left_percent}% left (reset {self._format_reset(limit.get('resets_at'))})"
            )
        return " | ".join(parts)

    @staticmethod
    def _label_for_window(minutes):
        if minutes is None:
            return "Unknown"
        if minutes >= 10080:
            return "Weekly"
        if 240 <= minutes <= 360:
            return "5h"
        return f"{minutes}m"

    @staticmethod
    def _format_reset(resets_at):
        if not isinstance(resets_at, (int, float)):
            return "unknown"
        try:
            return datetime.fromtimestamp(resets_at).strftime("%Y-%m-%d %H:%M")
        except Exception:
            return "unknown"
