"""Helpers for pytest tests."""

import os

import pytest


@pytest.fixture(scope='session')
def testdata_dir():
    """Path to the testdata directory."""
    return os.path.join(os.path.dirname(__file__), 'testdata')
