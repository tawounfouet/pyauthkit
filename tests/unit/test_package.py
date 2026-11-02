from importlib.metadata import version

import pyauthkit


def test_package_version_matches_metadata() -> None:
    assert pyauthkit.__version__ == version("pyauthkit")
