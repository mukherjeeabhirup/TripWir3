"""Legacy protocol tests explicitly select the mocked Nano alternative.

New routing tests pass Lightning explicitly and clear this test-only selector
when asserting production defaults. This file never preflights a live model.
"""
import pytest


@pytest.fixture(autouse=True)
def mocked_legacy_local_profile(monkeypatch):
    monkeypatch.setenv('TRIPWIR3_LOCAL_PROFILE','nano3_mlx')
