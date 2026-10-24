import pytest

def pytest_addoption(parser):
    parser.addoption("--live", action="store_true", default=False,
                     help="include tests hitting archive.org")

@pytest.fixture
def live(request):
    if not request.config.getoption("--live"):
        pytest.skip("live network test (use --live)")
    return True
