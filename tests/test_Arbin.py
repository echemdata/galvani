"""Tests for loading Arbin .res files."""

import os
import sqlite3
import subprocess

import pytest

from galvani import res2sqlite


have_mdbtools = (subprocess.call(['which', 'mdb-export'],
                                 stdout=subprocess.DEVNULL) == 0)


def test_res2sqlite_help():
    """Test running `res2sqlite --help`.

    This should work even when mdbtools is not installed.
    """
    help_output = subprocess.check_output(['res2sqlite', '--help'])
    assert b'Convert Arbin .res files to sqlite3 databases' in help_output


@pytest.mark.skipif(have_mdbtools, reason='This tests the failure when mdbtools is not installed')
def test_convert_Arbin_no_mdbtools(testdata_dir, tmpdir):
    """Checks that the conversion fails with an appropriate error message."""
    res_file = os.path.join(testdata_dir, 'arbin1.res')
    sqlite_file = os.path.join(str(tmpdir), 'arbin1.s3db')
    with pytest.raises(RuntimeError, match="Could not locate the `mdb-export` executable."):
        res2sqlite.convert_arbin_to_sqlite(res_file, sqlite_file)


@pytest.mark.skipif(not have_mdbtools, reason='Reading the Arbin file requires MDBTools')
@pytest.mark.parametrize('basename', ['arbin1', 'UM34_Test005E'])
def test_convert_Arbin_to_sqlite_function(testdata_dir, tmpdir, basename):
    """Convert an Arbin file to SQLite using the functional interface."""
    res_file = os.path.join(testdata_dir, basename + '.res')
    sqlite_file = os.path.join(str(tmpdir), basename + '.s3db')
    res2sqlite.convert_arbin_to_sqlite(res_file, sqlite_file)
    assert os.path.isfile(sqlite_file)
    with sqlite3.connect(sqlite_file) as conn:
        csr = conn.execute('SELECT * FROM Channel_Normal_Table;')
        csr.fetchone()


@pytest.mark.skipif(not have_mdbtools, reason='Reading the Arbin file requires MDBTools')
def test_convert_cmdline(testdata_dir, tmpdir):
    """Checks that the conversion fails with an appropriate error message."""
    res_file = os.path.join(testdata_dir, 'arbin1.res')
    sqlite_file = os.path.join(str(tmpdir), 'arbin1.s3db')
    subprocess.check_call(['res2sqlite', res_file, sqlite_file])
    assert os.path.isfile(sqlite_file)
    with sqlite3.connect(sqlite_file) as conn:
        csr = conn.execute('SELECT * FROM Channel_Normal_Table;')
        csr.fetchone()
