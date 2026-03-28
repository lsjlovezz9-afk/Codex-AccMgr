from __future__ import annotations

import json
import os
import platform
import re
import signal
import stat
import subprocess
import time
from pathlib import Path


class DesktopRefresher:
    def __init__(self, paths):
        self.paths = paths

    def refresh_after_auth_write(self, auth_path: Path, hold_seconds: float = 2.5) -> str:
        if os.name != "nt":
            return self.refresh_codex_app()

        self._set_readonly(auth_path, True)
        message = self.refresh_codex_app()
        time.sleep(hold_seconds)
        self._set_readonly(auth_path, False)
        return message

    def refresh_codex_app(self) -> str:
        try:
            if os.name == "nt":
                self._ensure_shell_snapshot_disabled()
                self._ensure_pencil_mcp_proxy()
                if self._restart_codex_desktop():
                    return "已重启 Codex 桌面端，账号将自动刷新。"
                pids = self._find_windows_codex_backend_pids()
                if not pids:
                    return (
                        "未检测到 Codex 后台进程，可能未启动或无权限。/"
                        " No Codex backend process found."
                    )
                for pid in pids:
                    self._stop_windows_process(pid)
                return (
                    "已请求 Codex 后台进程重启，账号将自动刷新。/"
                    " Codex backend restarted for auth refresh."
                )

            if platform.system() == "Darwin" and self._restart_codex_desktop_macos():
                return "已重启 Codex 桌面端，账号将自动刷新。"

            pids = self._find_unix_codex_backend_pids()
            if not pids:
                return (
                    "未检测到 Codex 后台进程，可能未启动或无权限。/"
                    " No Codex backend process found."
                )
            for pid in pids:
                try:
                    os.kill(pid, signal.SIGTERM)
                except Exception:
                    continue
            return (
                "已请求 Codex 后台进程重启，账号将自动刷新。/"
                " Codex backend restarted for auth refresh."
            )
        except Exception:
            return "自动刷新失败，请手动重启 Codex。/ Auto refresh failed, please restart Codex manually."

    @staticmethod
    def _set_readonly(path: Path, readonly: bool):
        try:
            if readonly:
                os.chmod(path, stat.S_IREAD)
            else:
                os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        except Exception:
            pass

    @staticmethod
    def _stop_windows_process(pid: int) -> None:
        for force in ("", " -Force"):
            try:
                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        f"Stop-Process -Id {pid}{force}",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                time.sleep(0.8)
            except Exception:
                continue

    def _ensure_pencil_mcp_proxy(self) -> bool:
        if os.name != "nt" or not self.paths.config_toml.exists():
            return False
        try:
            text = self.paths.config_toml.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return False
        if "[mcp_servers.pencil]" not in text:
            return False

        lines = text.splitlines(keepends=True)
        section_re = re.compile(r"^\s*\[([^\]]+)\]\s*$")
        cmd_re = re.compile(r'^\s*command\s*=\s*"(.*)"\s*$')
        args_re = re.compile(r'^\s*args\s*=\s*\[(.*)\]\s*$')

        start = None
        end = None
        for index, line in enumerate(lines):
            match = section_re.match(line)
            if match and match.group(1).strip() == "mcp_servers.pencil":
                start = index
                continue
            if start is not None and match:
                end = index
                break
        if start is None:
            return False
        if end is None:
            end = len(lines)

        cmd_line_idx = None
        args_line_idx = None
        cmd_value = None
        args_value: list[str] = []
        for index in range(start + 1, end):
            line = lines[index]
            match_cmd = cmd_re.match(line)
            if match_cmd:
                cmd_line_idx = index
                cmd_value = match_cmd.group(1)
                continue
            match_args = args_re.match(line)
            if match_args:
                args_line_idx = index
                args_value = re.findall(r'"([^"]*)"', match_args.group(1))

        if not cmd_value:
            return False
        if cmd_value.endswith("mcp_proxy.py") or any("mcp_proxy.py" in arg for arg in args_value):
            return True

        proxy_path = (Path(__file__).resolve().parent / "mcp_proxy.py").resolve()
        new_cmd = "py"
        new_args = ["-3", str(proxy_path), "--", cmd_value, *args_value]

        def toml_quote(value: str) -> str:
            return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\""

        if cmd_line_idx is None or args_line_idx is None:
            return False

        lines[cmd_line_idx] = f"command = {toml_quote(new_cmd)}\n"
        lines[args_line_idx] = "args = [ " + ", ".join(toml_quote(arg) for arg in new_args) + " ]\n"

        backup_path = self.paths.accounts_dir / "pencil_mcp_original.json"
        try:
            backup_path.write_text(
                json.dumps({"command": cmd_value, "args": args_value}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self.paths.config_toml.write_text("".join(lines), encoding="utf-8")
        except Exception:
            return False
        return True

    def _ensure_shell_snapshot_disabled(self) -> bool:
        if not self.paths.config_toml.exists():
            return False
        try:
            text = self.paths.config_toml.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return False

        line_re = re.compile(r"^\s*shell_snapshot\s*=\s*(true|false)\s*$", re.IGNORECASE | re.MULTILINE)
        if line_re.search(text):
            new_text = line_re.sub("shell_snapshot = false", text)
        else:
            suffix = "\n" if text.endswith("\n") else "\n\n"
            new_text = text + f"{suffix}shell_snapshot = false\n"

        if new_text == text:
            return True
        try:
            self.paths.config_toml.write_text(new_text, encoding="utf-8")
            return True
        except Exception:
            return False

    @staticmethod
    def _restart_codex_desktop() -> bool:
        command = (
            "$pkg = Get-AppxPackage -Name OpenAI.Codex -ErrorAction SilentlyContinue;"
            "Get-Process -Name Codex,codex -ErrorAction SilentlyContinue | Stop-Process;"
            "Start-Sleep -Milliseconds 500;"
            "Get-Process -Name Codex,codex -ErrorAction SilentlyContinue | Stop-Process -Force;"
            "if ($pkg) { Start-Process \"shell:AppsFolder\\$($pkg.PackageFamilyName)!App\"; };"
            "Start-Sleep -Milliseconds 800;"
            "if (Get-Process -Name Codex -ErrorAction SilentlyContinue) { Write-Output 'OK' }"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                check=False,
                capture_output=True,
                text=True,
            )
            return "OK" in (result.stdout or "")
        except Exception:
            return False

    @staticmethod
    def _restart_codex_desktop_macos() -> bool:
        try:
            subprocess.run(
                ["osascript", "-e", 'quit app "Codex"'],
                check=False,
                capture_output=True,
                text=True,
            )
            time.sleep(0.6)
            subprocess.run(
                ["open", "-a", "Codex"],
                check=False,
                capture_output=True,
                text=True,
            )
            time.sleep(0.6)
            return True
        except Exception:
            return False

    @staticmethod
    def _find_windows_codex_backend_pids() -> list[int]:
        command = (
            "$ids = @();"
            "$procs = Get-Process -Name codex -ErrorAction SilentlyContinue | Where-Object {"
            "  $p = $_.Path; if (-not $p) { $p = '' };"
            "  $p -match 'resources\\\\\\\\codex\\.exe' -or $p -match 'app\\\\\\\\asar\\\\\\\\unpacked\\\\\\\\codex'"
            "};"
            "if ($procs) { $ids += $procs | Select-Object -ExpandProperty Id };"
            "if (-not $ids) {"
            "  try {"
            "    $cim = Get-CimInstance Win32_Process -Filter \"Name='codex.exe'\" | "
            "      Select-Object ProcessId,ExecutablePath,CommandLine;"
            "    foreach ($p in $cim) {"
            "      $exe = $p.ExecutablePath; if (-not $exe) { $exe = '' };"
            "      $cmd = $p.CommandLine; if (-not $cmd) { $cmd = '' };"
            "      $path = $exe + ' ' + $cmd;"
            "      if ($path -match 'resources\\\\\\\\codex\\.exe' -or $path -match 'app\\.asar\\.unpacked\\\\\\\\codex' -or $cmd -match 'app-server') {"
            "        $ids += $p.ProcessId"
            "      }"
            "    }"
            "  } catch { }"
            "};"
            "if (-not $ids) {"
            "  try {"
            "    $fallback = Get-Process -Name codex -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id;"
            "    if ($fallback) { $ids += $fallback }"
            "  } catch { }"
            "};"
            "$ids | Sort-Object -Unique"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                check=False,
                capture_output=True,
                text=True,
            )
        except Exception:
            return []
        pids: list[int] = []
        for line in (result.stdout or "").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                pids.append(int(line))
            except ValueError:
                continue
        return pids

    @staticmethod
    def _find_unix_codex_backend_pids() -> list[int]:
        try:
            result = subprocess.run(
                ["ps", "-ax", "-o", "pid=", "-o", "command="],
                check=False,
                capture_output=True,
                text=True,
            )
        except Exception:
            return []
        pids: list[int] = []
        for line in (result.stdout or "").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            pid_str, command = parts
            if "/resources/codex" not in command and "/resources/app.asar.unpacked/codex" not in command:
                continue
            if "Codex.app/Contents/MacOS/Codex" in command:
                continue
            try:
                pids.append(int(pid_str))
            except ValueError:
                continue
        return pids
