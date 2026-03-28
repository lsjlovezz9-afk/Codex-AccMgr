# Codex AccMgr
[中文](#中文) | [English](#english)

---

## 中文

简洁、跨平台的 Codex 多账号切换命令行工具。

### ⚙️ 环境依赖
- 本工具基于 Python 编写，运行前需确保已安装 **[Python 3.10+](https://www.python.org/downloads/)**。
- 无第三方依赖库，无需额外执行 `pip install`，下载即用。
- GUI 入口为可选能力，若需要请安装 `PySide6` 或执行 `python -m pip install -e .[gui]`。

### ✨ 核心功能
- **轻量管理**：仅保存 `auth.json`，单账号占用极小。
- **智能识别**：自动从 JWT 解析邮箱并识别当前账号。
- **状态展示**：直观显示订阅类型 (Team/Plus/Pro/Free) 及剩余额度。
- **极简交互**：双语菜单，操作简单直观。
- **跨平台**：提供 Windows/macOS/Linux 一键运行脚本。
- **自动刷新**：切换账号后自动重启 Codex 桌面端以完成账号刷新，Windows 已验证，macOS 未测试。

### 🚀 快速开始

#### 方式 1：一键自动安装 (推荐)
能自动检测环境、下载工具，并为您配置好系统全局命别名 `codex-accmgr`。
* **Windows (PowerShell)**:
  ```powershell
  irm https://raw.githubusercontent.com/lsjlovezz9-afk/Codex-AccMgr/main/install.ps1 | iex
  ```
* **macOS / Linux (Terminal)**:
  ```bash
  bash -c "$(curl -fsSL https://raw.githubusercontent.com/lsjlovezz9-afk/Codex-AccMgr/main/install.sh)"
  ```
> 💡 **安装成功后**，只需在任何终端输入 `codex-accmgr` 即可随时召唤切换器！

#### 方式 2：本地克隆运行 (绿色免安装)
如果你不想使用自动脚本，可以直接下载源码在本地运行：
1. **获取代码**：
   ```bash
   git clone https://github.com/lsjlovezz9-afk/Codex-AccMgr.git
   cd Codex-AccMgr
   ```
   *(或者在网页端点击 `Code` -> `Download ZIP` 解压)*
2. **运行工具**：
   - **Windows**: 双击运行目录下的 `run.bat`，或者在终端执行 `set PYTHONPATH=src && python -m codex_accmgr`
   - **macOS / Linux**: 在终端执行 `chmod +x run.sh && ./run.sh`，或者执行 `PYTHONPATH=src python3 -m codex_accmgr`
   - **兼容入口**: `python codex.py`
   - **可编辑安装**: `python -m pip install -e .` 后可直接使用 `codex-accmgr`
   - **GUI 入口**: `PYTHONPATH=src python -m codex_accmgr.gui`

### 📖 使用说明

#### 💡 如何登录并保存新账号？（重要指引）
1. **保存当前账号**：请**不要**在 Codex 软件内点击“退出登录(Logout)”。而是先运行本工具，按 `2` 将当前已登录的账号添加并起个别名（如 `work`）。
2. **清空登录状态**：运行本工具，按 `4` (切换账号)，然后选择 `0` (默认/干净状态)。
3. **登录新账号**：重新打开 Codex 软件，此时软件会提示重新登录。登录你的新账号。
4. **保存新账号**：再次运行本工具，按 `2` 把刚登录的新账号也添加进来并起个别名（如 `gmail`）。
5. **自由切换**：以后就可以直接通过按 `4` 在这些收录的账号间自由切换了！

### 📁 目录结构

```text
.codex/
└── codex-accmgr/          # 账号存储目录
    ├── gmail/auth.json     # 对应别名的认证文件
    └── ...

codex-accmgr/
├── codex.py                          # 兼容 CLI 薄封装入口
├── run.bat / run.sh                  # 模块化运行脚本
├── src/codex_accmgr/                 # 主包目录
│   ├── domain/                       # 纯业务规则与模型
│   ├── application/                  # 用例编排
│   ├── infrastructure/               # 文件/进程/系统适配
│   └── presentation/                 # CLI / GUI 入口
├── config/accounts.json              # 账号列表配置
└── pyproject.toml                    # 包声明与入口脚本
```

### 💻 界面预览

```text
+--------------------------------------------------+
| Codex AccMgr                             v1.1.0  |
| account manager                                 |
+--------------------------------------------------+
Current Account / 当前账号:
 Alias / 别名 |  Email / 邮箱      |  Plan / 订阅 | Usage / 额度
 hotmail      |  ABC**@hotmail.com |  free        | Weekly: 90.0% left (reset 2026-03-15)
==================================================

[1] 查看账号 / List Accounts
[2] 添加账号 / Add Account
[3] 删除账号 / Remove Account
[4] 切换账号 / Switch Account
[q] 退出程序 / Exit
```

### ⚠️ 注意事项
- 额度数据读取自本地 `~/.codex/sessions` 日志，显示可能存在少许延迟。
- 邮箱默认掩码显示（前 2-3 位 + **）以保护隐私。
- 工具**不上传任何数据**，所有数据及凭证仅在本地保存。

### 📄 许可证
本项目采用 [MIT License](LICENSE) 许可证。

---

## English

A lightweight, cross-platform CLI for managing and switching multiple Codex accounts.

### ⚙️ Prerequisites
- This tool is written in Python. You must have **[Python 3.10+](https://www.python.org/downloads/)** installed before running it.
- No third-party dependencies are required (`pip install` is not needed), just download and run.
- The GUI entry point is optional. Install `PySide6` or run `python -m pip install -e .[gui]` if you want it.

### ✨ Core Features
- **Lightweight**: Only keeps `auth.json` with minimal disk usage.
- **Auto Parse**: Automatically parses email from JWT to identify the current account.
- **Status Display**: Intuitively shows subscription plan (Team/Plus/Pro/Free) and remaining usage.
- **Interactive UI**: Bilingual menu with simple, intuitive operations.
- **Cross-platform**: Provides one-click run scripts for Windows/macOS/Linux.
- **Auto Refresh**: Automatically restarts the Codex desktop app after switching to apply the new account. Verified on Windows, untested on macOS.

### 🚀 Quick Start

#### Method 1: One-Click Install (Recommended)
Automatically detects your environment, downloads the tool, and sets up a global `codex-accmgr` command alias.
* **Windows (PowerShell)**:
  ```powershell
  irm https://raw.githubusercontent.com/lsjlovezz9-afk/Codex-AccMgr/main/install.ps1 | iex
  ```
* **macOS / Linux (Terminal)**:
  ```bash
  bash -c "$(curl -fsSL https://raw.githubusercontent.com/lsjlovezz9-afk/Codex-AccMgr/main/install.sh)"
  ```
> 💡 **After successful installation**, simply type `codex-accmgr` in your terminal anytime to launch the switcher!

#### Method 2: Manual Clone & Run (Portable)
If you prefer not to use the automated scripts, you can download the source and run it locally:
1. **Get the code**:
   ```bash
   git clone https://github.com/lsjlovezz9-afk/Codex-AccMgr.git
   cd Codex-AccMgr
   ```
   *(Or click `Code` -> `Download ZIP` on the web interface to extract horizontally)*
2. **Run the tool**:
   - **Windows**: Double-click `run.bat`, or run `set PYTHONPATH=src && python -m codex_accmgr` in your terminal.
   - **macOS / Linux**: Run `chmod +x run.sh && ./run.sh`, or run `PYTHONPATH=src python3 -m codex_accmgr`.
   - **Compatibility entry**: `python codex.py`
   - **Editable install**: run `python -m pip install -e .`, then launch `codex-accmgr`
   - **GUI entry**: `PYTHONPATH=src python -m codex_accmgr.gui`

### 📖 Usage

#### 💡 How to login and save a new account? (Important Guide)
1. **Save current account**: Please **DO NOT** click "Logout" inside the Codex app. Instead, run this tool first, press `2` to add your currently logged-in account and give it an alias (e.g., `work`).
2. **Clear auth state**: Run this tool, press `4` (Switch Account), and select `0` (Default/Clean state).
3. **Login new account**: Reopen the Codex app. It will now ask you to log in. Log into your new account.
4. **Save new account**: Run this tool again, press `2` to add this newly logged-in account and give it an alias (e.g., `gmail`).
5. **Switch freely**: From now on, you can simply press `4` to freely switch between your saved accounts!

*(After switching accounts, the tool will attempt to refresh Codex so changes take effect immediately; if the Pencil MCP server is detected, a compatibility proxy is added and PowerShell shell_snapshot is disabled; on Windows/macOS it will prefer an automatic Codex desktop restart to avoid error pages.)*

### 📁 Directory Layout

```text
.codex/
└── codex-accmgr/          # Account storage
    ├── gmail/auth.json     # Auth file for the alias
    └── ...

codex-accmgr/
├── codex.py                          # Compatibility CLI shim
├── run.bat / run.sh                  # Module-based runners
├── src/codex_accmgr/                 # Main package
│   ├── domain/                       # Pure business rules and models
│   ├── application/                  # Use-case orchestration
│   ├── infrastructure/               # Files, processes, and system adapters
│   └── presentation/                 # CLI / GUI entry points
├── config/accounts.json              # Account list configuration
└── pyproject.toml                    # Package metadata and entry points
```

### 💻 UI Preview

```text
+--------------------------------------------------+
| Codex AccMgr                             v1.1.0  |
| account manager                                 |
+--------------------------------------------------+
Current Account / 当前账号:
 Alias / 别名 |  Email / 邮箱      |  Plan / 订阅 | Usage / 额度
 hotmail      |  ABC**@hotmail.com |  free        | Weekly: 90.0% left (reset 2026-03-15)
==================================================

[1] 查看账号 / List Accounts
[2] 添加账号 / Add Account
[3] 删除账号 / Remove Account
[4] 切换账号 / Switch Account
[q] 退出程序 / Exit
```

### ⚠️ Notes
- Usage data is read from local `~/.codex/sessions` logs; display might lag slightly.
- Emails are masked by default (first 2-3 characters + **) to protect privacy.
- The tool **does not upload any data**; all data and credentials belong firmly on local storage.

### 📄 License
This project is licensed under the [MIT License](LICENSE).
