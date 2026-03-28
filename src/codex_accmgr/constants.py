from pathlib import Path

APP_NAME = "Codex AccMgr"
APP_ALIAS = "codex-accmgr"
APP_GUI_ALIAS = "codex-accmgr-gui"
APP_VERSION = "v1.1.0"
SUBTITLE = "account manager"
BANNER_WIDTH = 50
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "accounts.json"
