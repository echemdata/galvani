# -*- coding: utf-8 -*-

import os.path

import numpy as np
from numpy.testing import assert_array_almost_equal, assert_array_equal
from nose.tools import ok_, eq_, raises

from ..import MPTfile, MPRfile
from ..BioLogic import MPTfileCSV  # not exported

testdata_dir = os.path.join(os.path.dirname(__file__), 'testdata')


def test_open_MPT():
    mpt1, comments = MPTfile(os.path.join(testdata_dir, 'bio-logic1.mpt'))
    eq_(comments, [])
    eq_(mpt1.dtype.names, ("mode", "ox/red", "error", "control changes",
                           "Ns changes", "counter inc.", "time/s",
                           "control/V/mA", "Ewe/V", "dQ/mA.h", "P/W",
                           "I/mA", "(Q-Qo)/mA.h", "x"))


@raises(ValueError)
def test_open_MPT_fails_for_bad_file():
    mpt1 = MPTfile(os.path.join(testdata_dir, 'bio-logic1.mpr'))


def test_open_MPT_csv():
    mpt1, comments = MPTfileCSV(os.path.join(testdata_dir, 'bio-logic1.mpt'))
    eq_(comments, [])
    eq_(mpt1.fieldnames, ["mode", "ox/red", "error", "control changes",
                          "Ns changes", "counter inc.", "time/s",
                          "control/V/mA", "Ewe/V", "dq/mA.h", "P/W",
                          "<I>/mA", "(Q-Qo)/mA.h", "x"])


@raises(ValueError)
def test_open_MPT_csv_fails_for_bad_file():
    mpt1 = MPTfileCSV(os.path.join(testdata_dir, 'bio-logic1.mpr'))


def test_open_MPR():
    mpr1 = MPRfile(os.path.join(testdata_dir, 'bio-logic1.mpr'))


@raises(ValueError)
def test_open_MPR_fails_for_bad_file():
    mpr1 = MPRfile(os.path.join(testdata_dir, 'arbin1.res'))


def test_MPR_matches_MPT():
    mpr1 = MPRfile(os.path.join(testdata_dir, 'bio-logic1.mpr'))
    mpt1, comments = MPTfile(os.path.join(testdata_dir, 'bio-logic1.mpt'))

    assert_array_equal(mpr1.data["flags"] & 0x03, mpt1["mode"])
    assert_array_equal(np.array(mpr1.data["flags"] & 0x04, dtype=np.bool_),
                       mpt1["ox/red"])
    assert_array_equal(np.array(mpr1.data["flags"] & 0x08, dtype=np.bool_),
                       mpt1["error"])
    assert_array_equal(np.array(mpr1.data["flags"] & 0x10, dtype=np.bool_),
                       mpt1["control changes"])
    assert_array_equal(np.array(mpr1.data["flags"] & 0x20, dtype=np.bool_),
                       mpt1["Ns changes"])
    ## Nothing uses the 0x40 bit of the flags
    assert_array_equal(np.array(mpr1.data["flags"] & 0x80, dtype=np.bool_),
                       mpt1["counter inc."])

    assert_array_almost_equal(mpr1.data["time/s"],
                              mpt1["time/s"],
                              decimal=5)  # 5 digits in CSV

    assert_array_almost_equal(mpr1.data["control/V/mA"],
                              mpt1["control/V/mA"],
                              decimal=6)  # 32 bit float precision

    assert_array_almost_equal(mpr1.data["Ewe/V"],
                              mpt1["Ewe/V"],
                              decimal=6)  # 32 bit float precision

    assert_array_almost_equal(mpr1.data["dQ/mA.h"],
                              mpt1["dQ/mA.h"],
                              decimal=17)  # 64 bit float precision

    assert_array_almost_equal(mpr1.data["P/W"],
                              mpt1["P/W"],
                              decimal=10)  # 32 bit float precision for 1.xxE-5
