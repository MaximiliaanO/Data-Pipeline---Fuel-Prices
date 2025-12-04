import pytest, sys, os
from unittest.mock import MagicMock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

@pytest.fixture
def mock_connection():
    """Returns mock database-connection."""
    conn = MagicMock()
    return conn

@pytest.fixture
def mock_cursor():
    """Returns mock cursor."""
    cur = MagicMock()
    return cur