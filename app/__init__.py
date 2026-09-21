import sys
from pathlib import Path

# Add services/api to sys.path so submodules are discovered
_api_dir = Path(__file__).resolve().parent / "services" / "api"
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

# Extend package search path to include services/api/app
_real_app_dir = _api_dir / "app"
if _real_app_dir.is_dir() and str(_real_app_dir) not in __path__:
    __path__.insert(0, str(_real_app_dir))
