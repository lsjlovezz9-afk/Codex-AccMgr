import sys
import os
from pathlib import Path
from bin.service import CodexService
from scripts.install import install

USE_COLOR = sys.stdout.isatty() and os.getenv("NO_COLOR") is None
APP_NAME = "Codex AccMgr"
APP_ALIAS = "codex-accmgr"
APP_VERSION = "v1.1.0"
SUBTITLE = "account manager"
BANNER_WIDTH = 50

def _enable_ansi():
    if os.name == "nt":
        try:
            os.system("")
        except Exception:
            pass

def _style(text, *codes):
    if not USE_COLOR or not codes:
        return text
    return "\033[" + ";".join(codes) + "m" + text + "\033[0m"

def _banner():
    line = "+" + "-" * BANNER_WIDTH + "+"
    print(_style(line, "36"))
    print(_style(f"| {APP_NAME}{APP_VERSION:>{48 - len(APP_NAME)}} |", "36", "1"))
    print(_style(f"| {SUBTITLE:<48} |", "36"))
    print(_style(line, "36"))

def _section(title):
    print(_style(title, "36", "1"))
    print(_style("-" * BANNER_WIDTH, "2"))

def _mask_email(email):
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked = local[0] + "**" if local else "**"
    else:
        masked = local[:3] + "**"
    return masked + "@" + domain

def check_installation():
    profile = Path.home() / ".zshrc" if os.name != 'nt' else Path.home() / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
    if profile.exists():
        with open(profile, 'r') as f:
            if APP_ALIAS in f.read():
                return True
    return False

def interactive_menu():
    _enable_ansi()
    if not check_installation():
        print(f"{APP_NAME} is not installed in your shell profile. / {APP_NAME} 未在您的 Shell 配置文件中安装。")
        choice = input("Do you want to install it now? (y/n) / 是否现在安装？(y/n): ")
        if choice.lower() == 'y':
            install()
            return

    service = CodexService()
    while True:
        # 获取当前账号详细信息
        current_info = service.get_current_account_info()
        usage = service.get_usage_stats()
        
        print("")
        _banner()
        print(f"\n{'='*50}")
        print("Current Account / 当前账号:")
        print(" Alias / 别名 |  Email / 邮箱            |  Plan / 订阅 | Usage / 额度")
        print(
            f" {current_info['alias']:<12} |  "
            f"{_mask_email(current_info['email']):<23} |  "
            f"{current_info['plan']:<12}| "
            f"{usage}"
        )
        print(f"{'='*50}")
        print("")
        print("[1] 查看账号 / List Accounts")
        print("[2] 添加账号 / Add Account")
        print("[3] 删除账号 / Remove Account")
        print("[4] 切换账号 / Switch Account")
        print("[q] 退出程序 / Exit")
        print("")
        
        choice = input("Select an option / 请选择操作: ")
        
        if choice == '1':
            accounts = service.get_accounts()
            if not accounts:
                print("No accounts found / 未找到账号")
            else:
                _section("Account List")
                print(f"\n{'='*60}")
                print(f"{'Alias/别名':<15} {'Email/邮箱':<30} {'Plan/订阅':<10}")
                print(f"{'-'*60}")
                for alias, data in accounts.items():
                    email = data.get('email', 'Unknown')
                    plan = data.get('plan', 'Unknown')
                    # 标记当前账号
                    marker = " *" if email.lower() == current_info['email'].lower() else ""
                    print(f"{alias:<15} {email:<30} {plan:<10}{marker}")
                print(f"{'='*60}")
                print("* = Current account / * = 当前账号")
        elif choice == '2':
            alias = input("Enter alias for new account (q to cancel) / 输入新账号别名(q 取消): ")
            if alias.strip().lower() == "q":
                print("Canceled. / 已取消。")
                continue
            service.add_account(alias)
        elif choice == '3':
            accounts = service.get_accounts()
            if not accounts:
                print("No accounts found / 未找到账号")
                continue
            
            _section("Remove Account")
            print("\nSelect account to remove / 选择要删除的账号:")
            aliases = list(accounts.keys())
            for i, alias in enumerate(aliases):
                email = accounts[alias].get('email', 'Unknown')
                plan = accounts[alias].get('plan', 'Unknown')
                print(f"  {i+1}. {alias} ({email} - {plan})")
            print("  q. Cancel / 取消")
            
            idx = input("Select index / 选择序号: ")
            if idx.strip().lower() == 'q':
                print("Canceled. / 已取消。")
                continue
            if idx.isdigit() and 1 <= int(idx) <= len(aliases):
                service.remove_account(aliases[int(idx)-1])
            else:
                print("Invalid choice / 无效选择")
        elif choice == '4':
            accounts = service.get_accounts()
            
            _section("Switch Account")
            print("\nSelect account to switch / 选择要切换的账号:")
            print("  0. Default (Clean) / 默认 (干净环境)")
            aliases = list(accounts.keys())
            for i, alias in enumerate(aliases):
                email = accounts[alias].get('email', 'Unknown')
                plan = accounts[alias].get('plan', 'Unknown')
                print(f"  {i+1}. {alias} ({email} - {plan})")
            print("  q. Cancel / 取消")
            
            idx = input("Select index / 选择序号: ")
            if idx == '0':
                auth_file = Path.home() / ".codex" / "auth.json"
                if auth_file.exists():
                    auth_file.unlink()
                print("Switched to Default (Clean) environment. / 已切换到默认 (干净) 环境。")
                service.refresh_codex_app()
                print("You can now login with a new account. / 您现在可以登录新账号。")
            elif idx.strip().lower() == 'q':
                print("Canceled. / 已取消。")
                continue
            elif idx.isdigit() and 1 <= int(idx) <= len(aliases):
                service.switch_account(aliases[int(idx)-1])
            else:
                print("Invalid choice / 无效选择")
        elif choice.strip().lower() == 'q':
            print("Goodbye / 再见")
            break
        else:
            print("Invalid choice / 无效选择")

def main():
    interactive_menu()

if __name__ == "__main__":
    main()
