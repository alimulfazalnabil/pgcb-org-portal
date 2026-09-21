import sys
from pathlib import Path

# Add services/api to the head of sys.path
_api_dir = Path(__file__).resolve().parent.parent / "services" / "api"
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

import importlib.util
_main_path = _api_dir / "app" / "main.py"
_spec = importlib.util.spec_from_file_location("app.main", _main_path)
_module = importlib.util.module_from_spec(_spec)
sys.modules["app.main"] = _module
_spec.loader.exec_module(_module)

app = getattr(_module, "app")
