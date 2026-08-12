"""Smoke tests for Titan Core."""


def test_smoke_imports():
    """Verify core and cli modules can be imported successfully."""
    import core
    import cli

    assert core is not None
    assert cli is not None
