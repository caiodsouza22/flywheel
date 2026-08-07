"""Package version smoke test."""

import flywheel


def test_version_present() -> None:
    assert isinstance(flywheel.__version__, str)
    assert flywheel.__version__