# -*- coding: utf-8 -*-

import os.path
import re
from datetime import datetime

import numpy as np
from numpy.testing import assert_array_almost_equal, assert_array_equal
import pytest

from galvani import MPTfile, MPRfile
from galvani.BioLogic import MPTfileCSV, str3  # not exported

testdata_dir = os.path.join(os.path.dirname(__file__), 'testdata')


def test_open_MPT():
    mpt1, comments = MPTfile(os.path.join(testdata_dir, 'bio_logic1.mpt'))
    assert comments == []
    assert mpt1.dtype.names == (
        "mode", "ox/red", "error", "control changes", "Ns changes",
        "counter inc.", "time/s", "control/V/mA", "Ewe/V", "dQ/mA.h", "P/W",
        "I/mA", "(Q-Qo)/mA.h", "x",
    )


def test_open_MPT_fails_for_bad_file():
    with pytest.raises(ValueError, match='Bad first line'):
        MPTfile(os.path.join(testdata_dir, 'bio_logic1.mpr'))


def test_open_MPT_csv():
    mpt1, comments = MPTfileCSV(os.path.join(testdata_dir, 'bio_logic1.mpt'))
    assert comments == []
    assert mpt1.fieldnames == [
        "mode", "ox/red", "error", "control changes", "Ns changes",
        "counter inc.", "time/s", "control/V/mA", "Ewe/V", "dq/mA.h", "P/W",
        "<I>/mA", "(Q-Qo)/mA.h", "x",
    ]


def test_open_MPT_csv_fails_for_bad_file():
    with pytest.raises((ValueError, UnicodeDecodeError)):
        MPTfileCSV(os.path.join(testdata_dir, 'bio_logic1.mpr'))


@pytest.mark.parametrize('filename, startdate, enddate', [
    ('bio_logic1.mpr', '2011-10-29', '2011-10-31'),
    ('bio_logic2.mpr', '2012-09-27', '2012-09-27'),
    ('bio_logic3.mpr', '2013-03-27', '2013-03-27'),
    ('bio_logic4.mpr', '2011-11-01', '2011-11-02'),
    ('bio_logic5.mpr', '2013-01-28', '2013-01-28'),
    # bio_logic6.mpr has no end date because it does not have a VMP LOG module
    ('bio_logic6.mpr', '2012-09-11', None),
])
def test_MPR_dates(filename, startdate, enddate):
    """Check that the start and end dates in .mpr files are read correctly."""
    mpr = MPRfile(os.path.join(testdata_dir, filename))
    assert mpr.startdate.strftime('%Y-%m-%d') == startdate
    if enddate:
        mpr.enddate.strftime('%Y-%m-%d') == enddate
    else:
        assert not hasattr(mpr, 'enddate')


def test_open_MPR_fails_for_bad_file():
    with pytest.raises(ValueError, match='Invalid magic for .mpr file'):
        MPRfile(os.path.join(testdata_dir, 'arbin1.res'))


def timestamp_from_comments(comments):
    for line in comments:
        time_match = re.match(b'Acquisition started on : ([0-9/]+ [0-9:]+)', line)
        if time_match:
            timestamp = datetime.strptime(str3(time_match.group(1)),
                                          '%m/%d/%Y %H:%M:%S')
            return timestamp
    raise AttributeError("No timestamp in comments")


def assert_MPR_matches_MPT(mpr, mpt, comments):

    def assert_field_matches(fieldname, decimal):
        if fieldname in mpr.dtype.fields:
            assert_array_almost_equal(mpr.data[fieldname],
                                      mpt[fieldname],
                                      decimal=decimal)

    def assert_field_exact(fieldname):
        if fieldname in mpr.dtype.fields:
            assert_array_equal(mpr.data[fieldname], mpt[fieldname])

    assert_array_equal(mpr.get_flag("mode"), mpt["mode"])
    assert_array_equal(mpr.get_flag("ox/red"), mpt["ox/red"])
    assert_array_equal(mpr.get_flag("error"), mpt["error"])
    assert_array_equal(mpr.get_flag("control changes"), mpt["control changes"])
    if "Ns changes" in mpt.dtype.fields:
        assert_array_equal(mpr.get_flag("Ns changes"), mpt["Ns changes"])
    ## Nothing uses the 0x40 bit of the flags    
    assert_array_equal(mpr.get_flag("counter inc."), mpt["counter inc."])

    assert_array_almost_equal(mpr.data["time/s"],
                              mpt["time/s"],
                              decimal=2)  # 2 digits in CSV

    assert_field_matches("control/V/mA", decimal=6)
    assert_field_matches("control/V", decimal=6)

    assert_array_almost_equal(mpr.data["Ewe/V"],
                              mpt["Ewe/V"],
                              decimal=6)  # 32 bit float precision

    assert_field_matches("dQ/mA.h", decimal=17)  # 64 bit float precision
    assert_field_matches("P/W", decimal=10)  # 32 bit float precision for 1.xxE-5
    assert_field_matches("I/mA", decimal=6)  # 32 bit float precision
    
    assert_field_exact("cycle number")
    assert_field_matches("(Q-Qo)/C", decimal=6)  # 32 bit float precision
    
    try:
        assert timestamp_from_comments(comments) == mpr.timestamp
    except AttributeError:
        pass


@pytest.mark.parametrize('basename', [
    'bio_logic1',
    'bio_logic2',
    # No bio_logic3.mpt file
    'bio_logic4',
    # bio_logic5 and bio_logic6 are special cases
    'CV_C01',
    '121_CA_455nm_6V_30min_C01',
])
def test_MPR_matches_MPT(basename):
    """Check the MPR parser against the MPT parser.

    Load a binary .mpr file and a text .mpt file which should contain
    exactly the same data. Check that the loaded data actually match.
    """
    binpath = os.path.join(testdata_dir, basename + '.mpr')
    txtpath = os.path.join(testdata_dir, basename + '.mpt')
    mpr = MPRfile(binpath)
    mpt, comments = MPTfile(txtpath)
    assert_MPR_matches_MPT(mpr, mpt, comments)


def test_MPR5_matches_MPT5():
    mpr = MPRfile(os.path.join(testdata_dir, 'bio_logic5.mpr'))
    mpt, comments = MPTfile((re.sub(b'\tXXX\t', b'\t0\t', line) for line in
                             open(os.path.join(testdata_dir, 'bio_logic5.mpt'),
                                  mode='rb')))
    assert_MPR_matches_MPT(mpr, mpt, comments)


def test_MPR6_matches_MPT6():
    mpr = MPRfile(os.path.join(testdata_dir, 'bio_logic6.mpr'))
    mpt, comments = MPTfile(os.path.join(testdata_dir, 'bio_logic6.mpt'))
    mpr.data = mpr.data[:958]  # .mpt file is incomplete
    assert_MPR_matches_MPT(mpr, mpt, comments)
