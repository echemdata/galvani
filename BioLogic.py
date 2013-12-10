# -*- coding: utf-8 -*-
"""Code to read in data files from Bio-Logic instruments"""

__all__ = ['MPTfileCSV', 'MPTfile']

import re
import csv
from os import SEEK_SET, SEEK_CUR
import time
from datetime import date
from collections import OrderedDict

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


VMPmodule_hdr = np.dtype([('shortname', 'S10'),
                          ('longname', 'S25'),
                          ('length', '<u4'),
                          ('version', '<u4'),
                          ('date', 'S8')])


def VMPdata_dtype_from_colIDs(colIDs):
    dtype_dict = OrderedDict()
    for colID in colIDs:
        if colID in (1, 2, 3, 21, 31, 65):
            dtype_dict['flags'] = 'u1'
        elif colID in (131,):
            dtype_dict['flags2'] = '<u2'
        elif colID == 4:
            dtype_dict['time/s'] = '<f8'
        elif colID == 5:
            dtype_dict['control/V/mA'] = '<f4'
        elif colID == 6:
            dtype_dict['Ewe/V'] = '<f4'
        elif colID == 7:
            dtype_dict['dQ/mA.h'] = '<f8'
        elif colID == 70:
            dtype_dict['P/W'] = '<f4'
        else:
            raise NotImplementedError("column type %d not implemented" % colID)
    return np.dtype(list(dtype_dict.items()))    


def read_VMP_modules(fileobj, read_module_data=True):
    """Reads in module headers in the VMPmodule_hdr format. Yields a dict with
    the headers and offset for each module.

    N.B. the offset yielded is the offset to the start of the data i.e. after
    the end of the header. The data runs from (offset) to (offset+length)"""
    while True:
        module_magic = fileobj.read(len(b'MODULE'))
        if len(module_magic) == 0:  # end of file
            raise StopIteration
        elif module_magic != b'MODULE':
            raise ValueError("Found %r, expecting start of new VMP MODULE" % module_magic)

        hdr_bytes = fileobj.read(VMPmodule_hdr.itemsize)
        if len(hdr_bytes) < VMPmodule_hdr.itemsize:
            raise IOError("Unexpected end of file while reading module header")

        hdr = np.fromstring(hdr_bytes, dtype=VMPmodule_hdr, count=1)
        hdr_dict = dict(((n, hdr[n][0]) for n in VMPmodule_hdr.names))
        hdr_dict['offset'] = fileobj.tell()
        if read_module_data:
            hdr_dict['data'] = fileobj.read(hdr_dict['length'])
            if len(hdr_dict['data']) != hdr_dict['length']:
                raise IOError("""Unexpected end of file while reading data
                    current module: %s
                    length read: %d
                    length expected: %d""" % (hdr_dict['longname'],
                                              len(hdr_dict['data']),
                                              hdr_dict['length']))
            yield hdr_dict
        else:
            yield hdr_dict
            fileobj.seek(hdr_dict['offset'] + hdr_dict['length'], SEEK_SET)


class MPRfile:
    """Bio-Logic .mpr file

    The file format is not specified anywhere and has therefore been reverse
    engineered. Not all the fields are known.

    Attributes
    ==========
    modules - A list of dicts containing basic information about the 'modules'
              of which the file is composed.
    data - numpy record array of type VMPdata_dtype containing the main data
           array of the file.
    startdate - The date when the experiment started
    enddate - The date when the experiment finished
    """

    def __init__(self, file_or_path):
        if isinstance(file_or_path, str):
            mpr_file = open(file_or_path, 'rb')
        else:
            mpr_file = file_or_path

        mpr_magic = b'BIO-LOGIC MODULAR FILE\x1a                         \x00\x00\x00\x00'
        magic = mpr_file.read(len(mpr_magic))
        if magic != mpr_magic:
            raise ValueError('Invalid magic for .mpr file: %s' % magic)

        modules = list(read_VMP_modules(mpr_file))
        self.modules = modules
        settings_mod, = (m for m in modules if m['shortname'] == b'VMP Set   ')
        data_module, = (m for m in modules if m['shortname'] == b'VMP data  ')
        maybe_log_module = [m for m in modules if m['shortname'] == b'VMP LOG   ']

        n_data_points = np.fromstring(data_module['data'][:4], dtype='<u4')
        n_columns = int(data_module['data'][4])

        if data_module['version'] == 0:
            column_types = np.fromstring(data_module['data'][5:], dtype='u1',
                                         count=n_columns)
            remaining_headers = data_module['data'][5 + n_columns:100]
            main_data = data_module['data'][100:]
        elif data_module['version'] == 2:
            column_types = np.fromstring(data_module['data'][5:], dtype='<u2',
                                         count=n_columns)
            ## There is 405 bytes of data before the main array starts
            remaining_headers = data_module['data'][5 + 2 * n_columns:405]
            main_data = data_module['data'][405:]
        else:
            raise ValueError("Unrecognised version for data module: %d" %
                             data_module['version'])

        assert(not any(remaining_headers))
        self.dtype = VMPdata_dtype_from_colIDs(column_types)
        self.data = np.fromstring(main_data, dtype=self.dtype)
        assert(self.data.shape[0] == n_data_points)

        ## No idea what these 'column types' mean or even if they are actually
        ## column types at all
        self.version = int(data_module['version'])
        self.cols = column_types
        self.npts = n_data_points

        tm = time.strptime(str(settings_mod['date'],  encoding='ascii'),
                           '%m/%d/%y')
        self.startdate = date(tm.tm_year, tm.tm_mon, tm.tm_mday)

        if maybe_log_module:
            log_module, = maybe_log_module
            tm = time.strptime(str(log_module['date'],  encoding='ascii'),
                               '%m/%d/%y')
            self.enddate = date(tm.tm_year, tm.tm_mon, tm.tm_mday)
