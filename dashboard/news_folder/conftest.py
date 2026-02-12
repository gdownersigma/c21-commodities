"""Pytest configuration for news tests."""
import sys
from pathlib import Path

dashboard_path = str(Path(__file__).parent.parent)
if dashboard_path not in sys.path:
    sys.path.insert(0, dashboard_path)
