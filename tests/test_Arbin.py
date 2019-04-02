"""Tests for loading Arbin .res files."""

import os
import sqlite3
import subprocess
import sys

import pytest

from galvani import res2sqlite


# TODO - change to subprocess.DEVNULL when python 2 support is removed
have_mdbtools = (subprocess.call(['which', 'mdb-export'], stdout=None) == 0)


@pytest.mark.skipif(have_mdbtools, reason='This tests the failure when mdbtools is not installed')
def test_convert_Arbin_no_mdbtools(testdata_dir, tmpdir):
    """Checks that the conversion fails with an appropriate error message."""
    res_file = os.path.join(testdata_dir, 'arbin1.res')
    sqlite_file = os.path.join(str(tmpdir), 'arbin1.s3db')
    if sys.version_info >= (3, 3):
        expected_exception = FileNotFoundError
    else:
        expected_exception = OSError
    with pytest.raises(expected_exception, match="No such file or directory: 'mdb-export'"):
        res2sqlite.convert_arbin_to_sqlite(res_file, sqlite_file)


@pytest.mark.skipif(not have_mdbtools, reason='Reading the Arbin file requires MDBTools')
@pytest.mark.parametrize('basename', ['arbin1'])
def test_convert_Arbin_to_sqlite(testdata_dir, tmpdir, basename):
    """Convert an Arbin file to SQLite using the functional interface."""
    res_file = os.path.join(testdata_dir, basename + '.res')
    sqlite_file = os.path.join(str(tmpdir), basename + '.s3db')
    res2sqlite.convert_arbin_to_sqlite(res_file, sqlite_file)
    assert os.path.isfile(sqlite_file)
    with sqlite3.connect(sqlite_file) as conn:
        csr = conn.execute('SELECT * FROM Channel_Normal_Table;')
        csr.fetchone()
