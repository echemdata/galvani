# -*- coding: utf-8 -*-

import os.path
from datetime import date

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


def test_open_MPR1():
    mpr1 = MPRfile(os.path.join(testdata_dir, 'bio-logic1.mpr'))
    ## Check the dates as a basic test that it has been read properly
    eq_(mpr1.startdate, date(2011, 10, 29))
    eq_(mpr1.enddate, date(2011, 10, 31))


def test_open_MPR2():
    mpr2 = MPRfile(os.path.join(testdata_dir, 'bio-logic2.mpr'))
    ## Check the dates as a basic test that it has been read properly
    eq_(mpr2.startdate, date(2012, 9, 27))
    eq_(mpr2.enddate, date(2012, 9, 27))


def test_open_MPR3():
    mpr2 = MPRfile(os.path.join(testdata_dir, 'bio-logic3.mpr'))
    ## Check the dates as a basic test that it has been read properly
    eq_(mpr2.startdate, date(2013, 3, 27))
    eq_(mpr2.enddate, date(2013, 3, 27))


@raises(ValueError)
def test_open_MPR_fails_for_bad_file():
    mpr1 = MPRfile(os.path.join(testdata_dir, 'arbin1.res'))


def assert_MPR_matches_MPT(mpr, mpt):

    assert_array_equal(mpr.data["flags"] & 0x03, mpt["mode"])
    assert_array_equal(np.array(mpr.data["flags"] & 0x04, dtype=np.bool_),
                       mpt["ox/red"])
    assert_array_equal(np.array(mpr.data["flags"] & 0x08, dtype=np.bool_),
                       mpt["error"])
    assert_array_equal(np.array(mpr.data["flags"] & 0x10, dtype=np.bool_),
                       mpt["control changes"])
    assert_array_equal(np.array(mpr.data["flags"] & 0x20, dtype=np.bool_),
                       mpt["Ns changes"])
    ## Nothing uses the 0x40 bit of the flags
    assert_array_equal(np.array(mpr.data["flags"] & 0x80, dtype=np.bool_),
                       mpt["counter inc."])

    assert_array_almost_equal(mpr.data["time/s"],
                              mpt["time/s"],
                              decimal=5)  # 5 digits in CSV

    assert_array_almost_equal(mpr.data["control/V/mA"],
                              mpt["control/V/mA"],
                              decimal=6)  # 32 bit float precision

    assert_array_almost_equal(mpr.data["Ewe/V"],
                              mpt["Ewe/V"],
                              decimal=6)  # 32 bit float precision

    assert_array_almost_equal(mpr.data["dQ/mA.h"],
                              mpt["dQ/mA.h"],
                              decimal=17)  # 64 bit float precision

    assert_array_almost_equal(mpr.data["P/W"],
                              mpt["P/W"],
                              decimal=10)  # 32 bit float precision for 1.xxE-5


def test_MPR1_matches_MPT1():
    mpr1 = MPRfile(os.path.join(testdata_dir, 'bio-logic1.mpr'))
    mpt1, comments = MPTfile(os.path.join(testdata_dir, 'bio-logic1.mpt'))
    assert_MPR_matches_MPT(mpr1, mpt1)
    

def test_MPR2_matches_MPT2():
    mpr2 = MPRfile(os.path.join(testdata_dir, 'bio-logic2.mpr'))
    mpt2, comments = MPTfile(os.path.join(testdata_dir, 'bio-logic2.mpt'))
    assert_MPR_matches_MPT(mpr2, mpt2)
    