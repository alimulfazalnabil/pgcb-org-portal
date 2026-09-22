import sys
from pathlib import Path

# Repo root is parent of the root `app` folder
_repo_root = Path(__file__).resolve().parent.parent
_api_dir = _repo_root / "services" / "api"
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

# Extend package search path to include services/api/app
_real_app_dir = _api_dir / "app"
if _real_app_dir.is_dir() and str(_real_app_dir) not in __path__:
    __path__.insert(0, str(_real_app_dir))
