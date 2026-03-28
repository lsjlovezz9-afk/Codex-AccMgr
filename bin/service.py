import json
import os
import glob
import shutil
import stat
import base64
import subprocess
import signal
import time
import re
import platform
from datetime import datetime
from pathlib import Path
from .core import CodexCore

class CodexService:
    ACCOUNTS_DIR = "codex-accmgr"
    
    def __init__(self, config_path: str = "config/accounts.json"):
        self.config_path = Path(__file__).parent.parent / config_path
        self.config_path.parent.mkdir(exist_ok=True)
        if not self.config_path.exists():
            with open(self.config_path, 'w') as f:
                json.dump({}, f)
        
        self.accounts_dir = Path.home() / ".codex" / self.ACCOUNTS_DIR
        self.accounts_dir.mkdir(parents=True, exist_ok=True)

    def get_accounts(self):
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def save_accounts(self, accounts):
        with open(self.config_path, 'w') as f:
            json.dump(accounts, f, indent=4)

    @staticmethod
    def parse_jwt_email(jwt_token):
        try:
            payload = jwt_token.split('.')[1]
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload)
            data = json.loads(decoded)
            return data.get('email', '')
        except:
            return ''

    @staticmethod
    def parse_jwt_plan(jwt_token):
        try:
            payload = jwt_token.split('.')[1]
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload)
            data = json.loads(decoded)
            if 'https://api.openai.com/auth' in data:
                return data['https://api.openai.com/auth'].get('chatgpt_plan_type', 'unknown')
            return 'unknown'
        except:
            return 'unknown'

    def get_current_email_and_plan(self):
        auth_file = Path.home() / ".codex" / "auth.json"
        if not auth_file.exists():
            return None, None
        
        try:
            with open(auth_file, 'r') as f:
                data = json.load(f)
            id_token = data.get('tokens', {}).get('id_token', '')
            if id_token:
                return self.parse_jwt_email(id_token), self.parse_jwt_plan(id_token)
        except:
            pass
        return None, None

    def get_current_account_info(self):
        email, plan = self.get_current_email_and_plan()
        
        if not email:
            return {
                'alias': 'Not logged in / 未登录',
                'email': 'N/A',
                'plan': 'N/A'
            }
        
        accounts = self.get_accounts()
        for alias, data in accounts.items():
            if data.get('email', '').lower() == email.lower():
                return {
                    'alias': alias,
                    'email': email,
                    'plan': plan or data.get('plan', 'Unknown')
                }
        
        return {
            'alias': f'Unknown ({email.split("@")[0]})',
            'email': email,
            'plan': plan or 'Unknown'
        }

    @staticmethod
    def _remove_readonly(func, path, excinfo):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def add_account(self, alias):
        accounts = self.get_accounts()
        if alias in accounts:
            print(f"Alias '{alias}' already exists. / 别名 '{alias}' 已存在。")
            return False

        codex_dir = Path.home() / ".codex"
        auth_file = codex_dir / "auth.json"
        
        if not auth_file.exists():
            print(f"No auth.json found. Please login first. / 未找到 auth.json，请先登录账号。")
            return False
        
        with open(auth_file, 'r') as f:
            auth_data = json.load(f)
        id_token = auth_data.get('tokens', {}).get('id_token', '')
        email = self.parse_jwt_email(id_token)
        plan = self.parse_jwt_plan(id_token)
        
        if not email:
            print(f"Cannot parse email from auth.json. / 无法从 auth.json 解析邮箱。")
            return False
        
        account_dir = self.accounts_dir / alias
        if account_dir.exists():
            shutil.rmtree(account_dir, onerror=self._remove_readonly)
        account_dir.mkdir(parents=True)
        
        shutil.copy2(auth_file, account_dir / "auth.json")
        
        accounts[alias] = {
            "email": email,
            "plan": plan,
            "alias": alias
        }
        self.save_accounts(accounts)
        print(f"Account '{alias}' created. / 账号 '{alias}' 已创建。")
        print(f"  Email: {email}")
        print(f"  Plan: {plan}")
        return True

    def remove_account(self, alias):
        accounts = self.get_accounts()
        if alias in accounts:
            account_dir = self.accounts_dir / alias
            if account_dir.exists():
                shutil.rmtree(account_dir, onerror=self._remove_readonly)
            del accounts[alias]
            self.save_accounts(accounts)
            print(f"Account '{alias}' removed. / 账号 '{alias}' 已删除。")
        else:
            print(f"Account '{alias}' not found. / 未找到账号 '{alias}'。")

    def get_usage_stats(self):
        """解析会话日志获取额度信息"""
        session_dir = Path.home() / ".codex" / "sessions"
        
        # 递归查找所有 rollout-*.jsonl 文件
        log_files = []
        for root, dirs, files in os.walk(session_dir):
            for f in files:
                if f.startswith("rollout-") and f.endswith(".jsonl"):
                    log_files.append(os.path.join(root, f))
        
        if not log_files:
            return "N/A"
        
        # 按修改时间排序，取最新的
        log_files.sort(key=os.path.getmtime, reverse=True)
        
        try:
            with open(log_files[0], 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if not lines:
                    return "N/A"
                
                # 从后往前找包含 rate_limits 的行
                for line in reversed(lines):
                    try:
                        data = json.loads(line.strip())
                        if data.get('type') == 'event_msg' and 'payload' in data:
                            payload = data['payload']
                            if payload.get('type') == 'token_count':
                                rate_limits = payload.get('rate_limits', {})
                                primary = rate_limits.get('primary', {})
                                secondary = rate_limits.get('secondary', {})
                                
                                limits = []
                                if primary:
                                    limits.append(primary)
                                if secondary:
                                    limits.append(secondary)

                                def label_for_window(minutes):
                                    if minutes is None:
                                        return "Unknown"
                                    if minutes >= 10080:
                                        return "Weekly"
                                    if 240 <= minutes <= 360:
                                        return "5h"
                                    return f"{minutes}m"

                                parts = []
                                for lim in limits:
                                    used = lim.get('used_percent', 0)
                                    if used is None:
                                        used = 0
                                    try:
                                        used = float(used)
                                    except Exception:
                                        used = 0
                                    minutes = lim.get('window_minutes')
                                    label = label_for_window(minutes)
                                    left = round(max(0.0, 100.0 - used), 1)
                                    resets_at = lim.get('resets_at')
                                    reset_text = "unknown"
                                    if isinstance(resets_at, (int, float)):
                                        try:
                                            reset_text = datetime.fromtimestamp(resets_at).strftime("%Y-%m-%d %H:%M")
                                        except Exception:
                                            reset_text = "unknown"
                                    parts.append(f"{label}: {left}% left (reset {reset_text})")

                                return " | ".join(parts) if parts else "N/A"
                    except:
                        continue
                return "N/A"
        except:
            return "Error parsing logs / 日志解析错误"

    def switch_account(self, alias_or_fragment):
        accounts = self.get_accounts()
        
        matched_alias = None
        for alias in accounts.keys():
            if alias_or_fragment.lower() in alias.lower():
                matched_alias = alias
                break
        
        if not matched_alias:
            print(f"No account matched '{alias_or_fragment}'. / 未找到匹配 '{alias_or_fragment}' 的账号。")
            return
        
        target_auth = self.accounts_dir / matched_alias / "auth.json"
        
        if not target_auth.exists():
            print(f"No auth.json found for '{matched_alias}'. / 账号 '{matched_alias}' 未找到认证文件。")
            return
        
        codex_dir = Path.home() / ".codex"
        target_path = codex_dir / "auth.json"
        shutil.copy2(target_auth, target_path)
        try:
            # 强制更新时间戳，触发可能存在的文件监听刷新
            os.utime(target_path, None)
        except Exception:
            pass
        
        email = accounts[matched_alias].get('email', 'Unknown')
        plan = accounts[matched_alias].get('plan', 'Unknown')
        print(f"Successfully switched to account: {matched_alias} / 已成功切换至账号: {matched_alias}")
        print(f"  Email: {email}")
        print(f"  Plan: {plan}")
        self._refresh_with_auth_lock(target_path)
        self._verify_auth_persisted(expected_email=email)

    def refresh_codex_app(self):
        """尝试触发 Codex 立即刷新认证，无需重启主程序"""
        try:
            if os.name == "nt":
                self._ensure_shell_snapshot_disabled()
                self._ensure_pencil_mcp_proxy()
                if self._restart_codex_desktop():
                    print("已重启 Codex 桌面端，账号将自动刷新。")
                    return True
                pids = self._find_windows_codex_backend_pids()
                if not pids:
                    print("未检测到 Codex 后台进程，可能未启动或无权限。/ No Codex backend process found.")
                    return False
                for pid in pids:
                    try:
                        subprocess.run(
                            ["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {pid}"],
                            check=False,
                            capture_output=True,
                            text=True,
                        )
                        time.sleep(0.8)
                        subprocess.run(
                            ["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {pid} -Force"],
                            check=False,
                            capture_output=True,
                            text=True,
                        )
                    except Exception:
                        continue
                print("已请求 Codex 后台进程重启，账号将自动刷新。/ Codex backend restarted for auth refresh.")
                return True

            if platform.system() == "Darwin":
                if self._restart_codex_desktop_macos():
                    print("已重启 Codex 桌面端，账号将自动刷新。")
                    return True

            pids = self._find_unix_codex_backend_pids()
            if not pids:
                print("未检测到 Codex 后台进程，可能未启动或无权限。/ No Codex backend process found.")
                return False
            for pid in pids:
                try:
                    os.kill(pid, signal.SIGTERM)
                except Exception:
                    continue
            print("已请求 Codex 后台进程重启，账号将自动刷新。/ Codex backend restarted for auth refresh.")
            return True
        except Exception:
            print("自动刷新失败，请手动重启 Codex。/ Auto refresh failed, please restart Codex manually.")
            return False

    def _ensure_pencil_mcp_proxy(self):
        if os.name != "nt":
            return False
        config_path = Path.home() / ".codex" / "config.toml"
        if not config_path.exists():
            return False
        try:
            text = config_path.read_text(encoding="utf-8", errors="ignore")
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
        for i, line in enumerate(lines):
            m = section_re.match(line)
            if m and m.group(1).strip() == "mcp_servers.pencil":
                start = i
                continue
            if start is not None and m:
                end = i
                break
        if start is None:
            return False
        if end is None:
            end = len(lines)

        cmd_line_idx = None
        args_line_idx = None
        cmd_value = None
        args_value = []
        for i in range(start + 1, end):
            line = lines[i]
            m_cmd = cmd_re.match(line)
            if m_cmd:
                cmd_line_idx = i
                cmd_value = m_cmd.group(1)
                continue
            m_args = args_re.match(line)
            if m_args:
                args_line_idx = i
                args_value = re.findall(r'"([^"]*)"', m_args.group(1))
                continue

        if not cmd_value:
            return False
        if cmd_value.endswith("mcp_proxy.py") or any("mcp_proxy.py" in a for a in args_value):
            return True

        proxy_path = (Path(__file__).parent / "mcp_proxy.py").resolve()
        new_cmd = "py"
        new_args = ["-3", str(proxy_path), "--", cmd_value] + args_value

        def toml_quote(s: str) -> str:
            return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\""

        new_cmd_line = f"command = {toml_quote(new_cmd)}\n"
        new_args_line = "args = [ " + ", ".join(toml_quote(a) for a in new_args) + " ]\n"

        if cmd_line_idx is None or args_line_idx is None:
            return False

        lines[cmd_line_idx] = new_cmd_line
        lines[args_line_idx] = new_args_line

        backup_path = self.accounts_dir / "pencil_mcp_original.json"
        try:
            backup_path.write_text(
                json.dumps({"command": cmd_value, "args": args_value}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            config_path.write_text("".join(lines), encoding="utf-8")
        except Exception:
            return False
        return True

    @staticmethod
    def _restart_codex_desktop():
        cmd = (
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
                ["powershell", "-NoProfile", "-Command", cmd],
                check=False,
                capture_output=True,
                text=True,
            )
            return "OK" in (result.stdout or "")
        except Exception:
            return False

    @staticmethod
    def _restart_codex_desktop_macos():
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
    def _ensure_shell_snapshot_disabled():
        config_path = Path.home() / ".codex" / "config.toml"
        if not config_path.exists():
            return False
        try:
            text = config_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return False

        line_re = re.compile(r'^\s*shell_snapshot\s*=\s*(true|false)\s*$', re.IGNORECASE | re.MULTILINE)
        if line_re.search(text):
            new_text = line_re.sub("shell_snapshot = false", text)
        else:
            suffix = "\n" if text.endswith("\n") else "\n\n"
            new_text = text + f"{suffix}shell_snapshot = false\n"

        if new_text == text:
            return True
        try:
            config_path.write_text(new_text, encoding="utf-8")
            return True
        except Exception:
            return False

    def _verify_auth_persisted(self, expected_email: str, wait_seconds: float = 1.5):
        if not expected_email:
            return
        try:
            time.sleep(wait_seconds)
        except Exception:
            pass
        current_email, _ = self.get_current_email_and_plan()
        if not current_email:
            return
        if current_email.lower() == expected_email.lower():
            return
        print("Detected auth.json was overwritten by desktop cache. Please close and reopen Codex desktop, then retry.")

    def _refresh_with_auth_lock(self, auth_path: Path, hold_seconds: float = 2.5):
        """短暂锁定 auth.json 为只读，避免桌面端启动时回写旧账号"""
        if os.name != "nt":
            self.refresh_codex_app()
            return
        self._set_readonly(auth_path, True)
        self.refresh_codex_app()
        try:
            time.sleep(hold_seconds)
        except Exception:
            pass
        self._set_readonly(auth_path, False)

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
    def _find_windows_codex_backend_pids():
        cmd = (
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
                ["powershell", "-NoProfile", "-Command", cmd],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                pids = []
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        pids.append(int(line))
                    except ValueError:
                        continue
                return pids
        except Exception:
            return []
        return []

    @staticmethod
    def _find_unix_codex_backend_pids():
        try:
            result = subprocess.run(
                ["ps", "-ax", "-o", "pid=", "-o", "command="],
                check=False,
                capture_output=True,
                text=True,
            )
            pids = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.split(None, 1)
                if len(parts) != 2:
                    continue
                pid_str, cmd = parts
                if "/resources/codex" not in cmd and "/resources/app.asar.unpacked/codex" not in cmd:
                    continue
                if "Codex.app/Contents/MacOS/Codex" in cmd:
                    continue
                try:
                    pids.append(int(pid_str))
                except ValueError:
                    continue
            return pids
        except Exception:
            return []
