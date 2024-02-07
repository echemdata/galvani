# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2013-2020 Christopher Kerr <chris.kerr@mykolab.ch>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os.path
import re
from datetime import date, datetime

import numpy as np
from numpy.testing import assert_array_almost_equal, assert_array_equal, assert_allclose
import pytest

from galvani import BioLogic, MPTfile, MPRfile
from galvani.BioLogic import MPTfileCSV  # not exported


def test_open_MPT(testdata_dir):
    mpt1, comments = MPTfile(os.path.join(testdata_dir, "bio_logic1.mpt"))
    assert comments == []
    assert mpt1.dtype.names == (
        "mode",
        "ox/red",
        "error",
        "control changes",
        "Ns changes",
        "counter inc.",
        "time/s",
        "control/V/mA",
        "Ewe/V",
        "dQ/mA.h",
        "P/W",
        "I/mA",
        "(Q-Qo)/mA.h",
        "x",
    )


def test_open_MPT_fails_for_bad_file(testdata_dir):
    with pytest.raises(ValueError, match="Bad first line"):
        MPTfile(os.path.join(testdata_dir, "bio_logic1.mpr"))


def test_open_MPT_csv(testdata_dir):
    mpt1, comments = MPTfileCSV(os.path.join(testdata_dir, "bio_logic1.mpt"))
    assert comments == []
    assert mpt1.fieldnames == [
        "mode",
        "ox/red",
        "error",
        "control changes",
        "Ns changes",
        "counter inc.",
        "time/s",
        "control/V/mA",
        "Ewe/V",
        "dq/mA.h",
        "P/W",
        "<I>/mA",
        "(Q-Qo)/mA.h",
        "x",
    ]


def test_open_MPT_csv_fails_for_bad_file(testdata_dir):
    with pytest.raises((ValueError, UnicodeDecodeError)):
        MPTfileCSV(os.path.join(testdata_dir, "bio_logic1.mpr"))


def test_colID_map_uniqueness():
    """Check some uniqueness properties of the VMPdata_colID_xyz maps."""
    field_colIDs = set(BioLogic.VMPdata_colID_dtype_map.keys())
    flag_colIDs = set(BioLogic.VMPdata_colID_flag_map.keys())
    field_names = [v[0] for v in BioLogic.VMPdata_colID_dtype_map.values()]
    flag_names = [v[0] for v in BioLogic.VMPdata_colID_flag_map.values()]
    assert not field_colIDs.intersection(flag_colIDs)
    # 'I/mA' and 'dQ/mA.h' are duplicated
    # assert len(set(field_names)) == len(field_names)
    assert len(set(flag_names)) == len(flag_names)
    assert not set(field_names).intersection(flag_names)


@pytest.mark.parametrize(
    "colIDs, expected",
    [
        ([1, 2, 3], [("flags", "u1")]),
        ([4, 6], [("time/s", "<f8"), ("Ewe/V", "<f4")]),
        ([1, 4, 21], [("flags", "u1"), ("time/s", "<f8")]),
        ([4, 6, 4], [("time/s", "<f8"), ("Ewe/V", "<f4"), ("time/s 2", "<f8")]),
        ([4, 9999], NotImplementedError),
    ],
)
def test_colID_to_dtype(colIDs, expected):
    """Test converting column ID to numpy dtype."""
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            BioLogic.VMPdata_dtype_from_colIDs(colIDs)
        return
    expected_dtype = np.dtype(expected)
    dtype, flags_dict = BioLogic.VMPdata_dtype_from_colIDs(colIDs)
    assert dtype == expected_dtype


@pytest.mark.parametrize(
    "data, expected",
    [
        ("02/23/17", date(2017, 2, 23)),
        ("10-03-05", date(2005, 10, 3)),
        ("11.12.20", date(2020, 11, 12)),
        (b"01/02/03", date(2003, 1, 2)),
        ("13.08.07", ValueError),
        ("03-04/05", ValueError),
    ],
)
def test_parse_BioLogic_date(data, expected):
    """Test the parse_BioLogic_date function."""
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            BioLogic.parse_BioLogic_date(data)
        return
    result = BioLogic.parse_BioLogic_date(data)
    assert result == expected


@pytest.mark.parametrize(
    "filename, startdate, enddate",
    [
        ("bio_logic1.mpr", "2011-10-29", "2011-10-31"),
        ("bio_logic2.mpr", "2012-09-27", "2012-09-27"),
        ("bio_logic3.mpr", "2013-03-27", "2013-03-27"),
        ("bio_logic4.mpr", "2011-11-01", "2011-11-02"),
        ("bio_logic5.mpr", "2013-01-28", "2013-01-28"),
        # bio_logic6.mpr has no end date because it does not have a VMP LOG module
        ("bio_logic6.mpr", "2012-09-11", None),
        # C019P-0ppb-A_C01.mpr stores the date in a different format
        ("C019P-0ppb-A_C01.mpr", "2019-03-14", "2019-03-14"),
        ("Rapp_Error.mpr", "2010-12-02", "2010-12-02"),
        ("Ewe_Error.mpr", "2021-11-18", "2021-11-19"),
        ("col_27_issue_74.mpr", "2022-07-28", "2022-07-28"),
    ],
)
def test_MPR_dates(testdata_dir, filename, startdate, enddate):
    """Check that the start and end dates in .mpr files are read correctly."""
    mpr = MPRfile(os.path.join(testdata_dir, filename))
    assert mpr.startdate.strftime("%Y-%m-%d") == startdate
    if enddate:
        assert mpr.enddate.strftime("%Y-%m-%d") == enddate
    else:
        assert not hasattr(mpr, "enddate")


def test_open_MPR_fails_for_bad_file(testdata_dir):
    with pytest.raises(ValueError, match="Invalid magic for .mpr file"):
        MPRfile(os.path.join(testdata_dir, "arbin1.res"))


def timestamp_from_comments(comments):
    for line in comments:
        time_match = re.match(b"Acquisition started on : ([0-9/]+ [0-9:]+)", line)
        if time_match:
            timestamp = datetime.strptime(
                time_match.group(1).decode("ascii"), "%m/%d/%Y %H:%M:%S"
            )
            return timestamp
    raise AttributeError("No timestamp in comments")


def assert_MPR_matches_MPT(mpr, mpt, comments):
    def assert_field_matches(fieldname, decimal):
        if fieldname in mpr.dtype.fields:
            assert_array_almost_equal(
                mpr.data[fieldname], mpt[fieldname], decimal=decimal
            )

    def assert_field_exact(fieldname):
        if fieldname in mpr.dtype.fields:
            assert_array_equal(mpr.data[fieldname], mpt[fieldname])

    assert_array_equal(mpr.get_flag("mode"), mpt["mode"])
    assert_array_equal(mpr.get_flag("ox/red"), mpt["ox/red"])
    assert_array_equal(mpr.get_flag("error"), mpt["error"])
    assert_array_equal(mpr.get_flag("control changes"), mpt["control changes"])
    if "Ns changes" in mpt.dtype.fields:
        assert_array_equal(mpr.get_flag("Ns changes"), mpt["Ns changes"])
    # Nothing uses the 0x40 bit of the flags
    assert_array_equal(mpr.get_flag("counter inc."), mpt["counter inc."])

    assert_array_almost_equal(
        mpr.data["time/s"], mpt["time/s"], decimal=2
    )  # 2 digits in CSV

    assert_field_matches("control/V/mA", decimal=6)
    assert_field_matches("control/V", decimal=6)

    assert_array_almost_equal(
        mpr.data["Ewe/V"], mpt["Ewe/V"], decimal=6
    )  # 32 bit float precision

    assert_field_matches("dQ/mA.h", decimal=16)  # 64 bit float precision
    assert_field_matches("P/W", decimal=10)  # 32 bit float precision for 1.xxE-5
    assert_field_matches("I/mA", decimal=6)  # 32 bit float precision

    assert_field_exact("cycle number")
    assert_field_matches("(Q-Qo)/C", decimal=6)  # 32 bit float precision

    try:
        assert timestamp_from_comments(comments) == mpr.timestamp.replace(microsecond=0)
    except AttributeError:
        pass


def assert_MPR_matches_MPT_v2(mpr, mpt, comments):
    """
    Asserts that the fields in the MPR.data ar the same as in the MPT.

    Modified from assert_MPR_matches_MPT. Automatically converts dtype from MPT data
    to dtype from MPR data before comparing the columns.

    Special case for EIS_indicators: these fields are valid only at f<100kHz so their
    values are replaced by -1 or 0 at high frequency in the MPT file, this is not the
    case in the MPR data.

    Parameters
    ----------
    mpr : MPRfile
        Data extracted with the MPRfile class.
    mpt : np.array
        Data extracted with MPTfile method.

    Returns
    -------
    None.

    """

    def assert_field_matches(fieldname):
        EIS_quality_indicators = [
            "THD Ewe/%",
            "NSD Ewe/%",
            "NSR Ewe/%",
            "|Ewe h2|/V",
            "|Ewe h3|/V",
            "|Ewe h4|/V",
            "|Ewe h5|/V",
            "|Ewe h6|/V",
            "|Ewe h7|/V",
            "THD I/%",
            "NSD I/%",
            "NSR I/%",
            "|I h2|/A",
            "|I h3|/A",
            "|I h4|/A",
            "|I h5|/A",
            "|I h6|/A",
            "|I h7|/A",
        ]

        if fieldname in EIS_quality_indicators:  # EIS quality indicators only valid for f < 100kHz
            index_inf_100k = np.where(mpr.data["freq/Hz"] < 100000)[0]
            assert_allclose(
                mpr.data[index_inf_100k][fieldname],
                mpt[index_inf_100k][fieldname].astype(mpr.data[fieldname].dtype),
            )
        elif fieldname == "<Ewe>/V":
            assert_allclose(
                mpr.data[fieldname],
                mpt["Ewe/V"].astype(mpr.data[fieldname].dtype),
            )
        elif fieldname == "<I>/mA":
            assert_allclose(
                mpr.data[fieldname],
                mpt["I/mA"].astype(mpr.data[fieldname].dtype),
            )
        elif fieldname == "dq/mA.h":
            assert_allclose(
                mpr.data[fieldname],
                mpt["dQ/mA.h"].astype(mpr.data[fieldname].dtype),
            )
        else:
            assert_allclose(
                mpr.data[fieldname],
                mpt[fieldname].astype(mpr.data[fieldname].dtype),
            )

    def assert_field_exact(fieldname):
        if fieldname in mpr.dtype.fields:
            assert_array_equal(mpr.data[fieldname], mpt[fieldname])

    for key in mpr.flags_dict.keys():
        assert_array_equal(mpr.get_flag(key), mpt[key])

    for d in mpr.dtype.descr[1:]:
        assert_field_matches(d[0])

    try:
        assert timestamp_from_comments(comments) == mpr.timestamp.replace(microsecond=0)
    except AttributeError:
        pass


@pytest.mark.parametrize(
    "basename",
    [
        "bio_logic1",
        "bio_logic2",
        # No bio_logic3.mpt file
        "bio_logic4",
        # bio_logic5 and bio_logic6 are special cases
        "CV_C01",
        "121_CA_455nm_6V_30min_C01",
        "020-formation_CB5",
    ],
)
def test_MPR_matches_MPT(testdata_dir, basename):
    """Check the MPR parser against the MPT parser.

    Load a binary .mpr file and a text .mpt file which should contain
    exactly the same data. Check that the loaded data actually match.
    """
    binpath = os.path.join(testdata_dir, basename + ".mpr")
    txtpath = os.path.join(testdata_dir, basename + ".mpt")
    mpr = MPRfile(binpath)
    mpt, comments = MPTfile(txtpath, encoding="latin1")
    assert_MPR_matches_MPT(mpr, mpt, comments)


def test_MPR5_matches_MPT5(testdata_dir):
    mpr = MPRfile(os.path.join(testdata_dir, "bio_logic5.mpr"))
    mpt, comments = MPTfile(
        (
            re.sub(b"\tXXX\t", b"\t0\t", line)
            for line in open(os.path.join(testdata_dir, "bio_logic5.mpt"), mode="rb")
        )
    )
    assert_MPR_matches_MPT(mpr, mpt, comments)


def test_MPR6_matches_MPT6(testdata_dir):
    mpr = MPRfile(os.path.join(testdata_dir, "bio_logic6.mpr"))
    mpt, comments = MPTfile(os.path.join(testdata_dir, "bio_logic6.mpt"))
    mpr.data = mpr.data[:958]  # .mpt file is incomplete
    assert_MPR_matches_MPT(mpr, mpt, comments)


@pytest.mark.parametrize(
    "basename_v1150",
    ["v1150_CA", "v1150_CP", "v1150_GCPL", "v1150_GEIS", "v1150_MB", "v1150_OCV", "v1150_PEIS"],
)
def test_MPR_matches_MPT_v1150(testdata_dir, basename_v1150):
    """Check the MPR parser against the MPT parser.

    Load a binary .mpr file and a text .mpt file which should contain
    exactly the same data. Check that the loaded data actually match.
    """
    binpath = os.path.join(testdata_dir, "v1150", basename_v1150 + ".mpr")
    txtpath = os.path.join(testdata_dir, "v1150", basename_v1150 + ".mpt")
    mpr = MPRfile(binpath)
    mpt, comments = MPTfile(txtpath, encoding="latin1")
    assert_MPR_matches_MPT_v2(mpr, mpt, comments)


def test_loop_from_file(testdata_dir):
    """Check if the loop_index is correctly extracted from the _LOOP.txt file
    """
    mpr = MPRfile(os.path.join(testdata_dir, "running", "running_OCV.mpr"))
    if mpr.loop_index is None:
        raise AssertionError("No loop_index found")
    elif not len(mpr.loop_index) == 4:
        raise AssertionError("loop_index is not the right size")
    elif not (mpr.loop_index == [0, 4, 8, 11]).all():
        raise AssertionError("loop_index values are wrong")


def test_timestamp_from_file(testdata_dir):
    """Check if the loop_index is correctly extracted from the _LOOP.txt file
    """
    mpr = MPRfile(os.path.join(testdata_dir, "running", "running_OCV.mpr"))
    if not hasattr(mpr, "timestamp"):
        raise AssertionError("No timestamp found")
    elif not mpr.timestamp.timestamp() == 1707299985.908:
        raise AssertionError("timestamp value is wrong")
