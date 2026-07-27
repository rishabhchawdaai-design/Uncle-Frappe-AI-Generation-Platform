import tempfile
import shutil
import pytest


@pytest.fixture
def ledger_isolated():
    """Provide an isolated temp directory for DecisionLedger tests."""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)
