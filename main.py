import sys
from pathlib import Path

_api_dir = Path(__file__).resolve().parent / "services" / "api"
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

from app.main import app
