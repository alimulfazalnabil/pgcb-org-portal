import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent
_api_dir = _repo_root / "services" / "api"
_real_app_dir = _api_dir / "app"

if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

# Ensure root package 'app' has services/api/app in its __path__
try:
    import app
    if _real_app_dir.is_dir() and str(_real_app_dir) not in app.__path__:
        app.__path__.insert(0, str(_real_app_dir))
except Exception:
    pass

import importlib.util
_main_path = _real_app_dir / "main.py"
_spec = importlib.util.spec_from_file_location("app.main", _main_path)
_module = importlib.util.module_from_spec(_spec)
sys.modules["app.main"] = _module
_spec.loader.exec_module(_module)

app = getattr(_module, "app")
