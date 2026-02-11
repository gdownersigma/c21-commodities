"""Pytest configuration for news tests."""
import sys
from pathlib import Path

# Add dashboard directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
