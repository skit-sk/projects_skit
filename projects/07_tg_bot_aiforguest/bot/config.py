import os
from pathlib import Path

PROJECT_DIR = Path(os.getenv("TG_PROJECT_DIR", Path(__file__).resolve().parent.parent))
WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", PROJECT_DIR.parent.parent))

_env_path = PROJECT_DIR / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

TOKEN = os.getenv("TG_BOT_TOKEN", "")
SUPER_USER = int(os.getenv("TG_SUPER_USER", "0"))
if not TOKEN:
    raise RuntimeError("TG_BOT_TOKEN not set")
if not SUPER_USER:
    raise RuntimeError("TG_SUPER_USER not set")

STATE_FILE = PROJECT_DIR / "bot" / "state.json"
UNAUTHORIZED_FILE = PROJECT_DIR / "bot" / "unauthorized.json"
TG_ALL_DIR = PROJECT_DIR / "TG_ALL"

DEFAULT_MODEL = "opencode/deepseek-v4-flash-free"
DEFAULT_MSG_LIMIT = 50
DEFAULT_TOKEN_LIMIT = 1_000_000
DEFAULT_STORAGE_MB = 500
DEFAULT_FILE_LIMIT = 1000
OPCODE_TIMEOUT = 180
