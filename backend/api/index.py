import os
import sys
from pathlib import Path

# Add backend root to sys.path so 'app' packages resolve properly
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
