"""Helpers for pytest tests."""

# SPDX-FileCopyrightText: 2019 Christopher Kerr <chris.kerr@mykolab.ch>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os

import pytest


@pytest.fixture(scope="session")
def testdata_dir():
    """Path to the testdata directory."""
    return os.path.join(os.path.dirname(__file__), "testdata")
