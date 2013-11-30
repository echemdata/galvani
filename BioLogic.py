# -*- coding: utf-8 -*-
"""Code to read in data files from Bio-Logic instruments"""

__all__ = ['MPTfileCSV', 'MPTfile']

import re
import csv

import numpy as np


def fieldname_to_dtype(fieldname):
    """Converts a column header from the MPT file into a tuple of
    canonical name and appropriate numpy dtype"""

    if fieldname == 'mode':
        return ('mode', np.uint8)
    elif fieldname in ("ox/red", "error", "control changes", "Ns changes",
                       "counter inc."):
        return (fieldname, np.bool_)
    elif fieldname in ("time/s", "Ewe/V", "P/W", "(Q-Qo)/mA.h", "x"):
        return (fieldname, np.float_)
    elif fieldname in ("dq/mA.h", "dQ/mA.h"):
        return ("dQ/mA.h", np.float_)
    elif fieldname in ("I/mA", "<I>/mA"):
        return ("I/mA", np.float_)
    elif fieldname in ("control/V", "control/V/mA"):
        return ("control/V/mA", np.float_)
    else:
        raise ValueError("Invalid column header: %s" % fieldname)


def MPTfile(file_or_path):
    """Opens .mpt files as numpy record arrays

    Checks for the correct headings, skips any comments and returns a
    numpy record array object and a list of comments
    """

    if isinstance(file_or_path, str):
        mpt_file = open(file_or_path, 'rb')
    else:
        mpt_file = file_or_path

    magic = next(mpt_file)
    if magic != b'EC-Lab ASCII FILE\r\n':
        raise ValueError("Bad first line for EC-Lab file: '%s'" % magic)

    nb_headers_match = re.match(b'Nb header lines : (\d+)\s*$', next(mpt_file))
    nb_headers = int(nb_headers_match.group(1))
    if nb_headers < 3:
        raise ValueError("Too few header lines: %d" % nb_headers)

    ## The 'magic number' line, the 'Nb headers' line and the column headers
    ## make three lines. Every additional line is a comment line.
    comments = [next(mpt_file) for i in range(nb_headers - 3)]

    fieldnames = next(mpt_file).decode('ascii').strip().split('\t')

    expected_fieldnames = (
        ["mode", "ox/red", "error", "control changes", "Ns changes",
         "counter inc.", "time/s", "control/V/mA", "Ewe/V", "dq/mA.h",
         "P/W", "<I>/mA", "(Q-Qo)/mA.h", "x"],
        ["mode", "ox/red", "error", "control changes", "Ns changes",
         "counter inc.", "time/s", "control/V", "Ewe/V", "I/mA",
         "dQ/mA.h", "P/W"],
        ["mode", "ox/red", "error", "control changes", "Ns changes",
         "counter inc.", "time/s", "control/V", "Ewe/V", "<I>/mA",
         "dQ/mA.h", "P/W"])
    if fieldnames not in expected_fieldnames:
        raise ValueError("Unrecognised headers for MPT file format %s" %
                         fieldnames)

    record_type = np.dtype(list(map(fieldname_to_dtype, fieldnames)))

    mpt_array = np.loadtxt(mpt_file, dtype=record_type)

    return mpt_array, comments


def MPTfileCSV(file_or_path):
    """Simple function to open MPT files as csv.DictReader objects

    Checks for the correct headings, skips any comments and returns a
    csv.DictReader object and a list of comments
    """

    if isinstance(file_or_path, str):
        mpt_file = open(file_or_path, 'r')
    else:
        mpt_file = file_or_path

    magic = next(mpt_file)
    if magic != 'EC-Lab ASCII FILE\n':
        raise ValueError("Bad first line for EC-Lab file: '%s'" % magic)

    nb_headers_match = re.match('Nb header lines : (\d+)\s*$', next(mpt_file))
    nb_headers = int(nb_headers_match.group(1))
    if nb_headers < 3:
        raise ValueError("Too few header lines: %d" % nb_headers)

    ## The 'magic number' line, the 'Nb headers' line and the column headers
    ## make three lines. Every additional line is a comment line.
    comments = [next(mpt_file) for i in range(nb_headers - 3)]

    mpt_csv = csv.DictReader(mpt_file, dialect='excel-tab')

    expected_fieldnames = (
        ["mode", "ox/red", "error", "control changes", "Ns changes",
         "counter inc.", "time/s", "control/V/mA", "Ewe/V", "dq/mA.h",
         "P/W", "<I>/mA", "(Q-Qo)/mA.h", "x"],
        ["mode", "ox/red", "error", "control changes", "Ns changes",
         "counter inc.", "time/s", "control/V", "Ewe/V", "I/mA",
         "dQ/mA.h", "P/W"],
        ["mode", "ox/red", "error", "control changes", "Ns changes",
         "counter inc.", "time/s", "control/V", "Ewe/V", "<I>/mA",
         "dQ/mA.h", "P/W"])
    if mpt_csv.fieldnames not in expected_fieldnames:
        raise ValueError("Unrecognised headers for MPT file format")

    return mpt_csv, comments
