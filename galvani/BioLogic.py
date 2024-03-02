# -*- coding: utf-8 -*-
"""Code to read in data files from Bio-Logic instruments"""

# SPDX-FileCopyrightText: 2013-2020 Christopher Kerr, "bcolsen"
#
# SPDX-License-Identifier: GPL-3.0-or-later

__all__ = ["MPTfileCSV", "MPTfile"]

import re
import csv
from os import SEEK_SET, path
import time
from datetime import date, datetime, timedelta
from collections import defaultdict, OrderedDict

import numpy as np


def fieldname_to_dtype(fieldname):
    """Converts a column header from the MPT file into a tuple of
    canonical name and appropriate numpy dtype"""

    if fieldname == "mode":
        return ("mode", np.uint8)
    elif fieldname in (
        "ox/red",
        "error",
        "control changes",
        "Ns changes",
        "counter inc.",
    ):
        return (fieldname, np.bool_)
    elif fieldname in (
        "time/s",
        "P/W",
        "(Q-Qo)/mA.h",
        "x",
        "control/V",
        "control/mA",
        "control/V/mA",
        "(Q-Qo)/C",
        "dQ/C",
        "freq/Hz",
        "|Ewe|/V",
        "|I|/A",
        "Phase(Z)/deg",
        "|Z|/Ohm",
        "Re(Z)/Ohm",
        "-Im(Z)/Ohm",
        "Re(M)",
        "Im(M)",
        "|M|",
        "Re(Permittivity)",
        "Im(Permittivity)",
        "|Permittivity|",
        "Tan(Delta)",
    ):
        return (fieldname, np.float_)
    elif fieldname in (
        "Q charge/discharge/mA.h",
        "step time/s",
        "Q charge/mA.h",
        "Q discharge/mA.h",
        "Temperature/°C",
        "Efficiency/%",
        "Capacity/mA.h",
        "Unk1",
        "rotation rate/rpm",
        "pad number",
    ):
        return (fieldname, np.float_)
    elif fieldname in ("cycle number", "I Range", "Ns", "half cycle", "z cycle"):
        return (fieldname, np.int_)
    elif fieldname in ("dq/mA.h", "dQ/mA.h"):
        return ("dQ/mA.h", np.float_)
    elif fieldname in ("I/mA", "<I>/mA"):
        return ("I/mA", np.float_)
    elif fieldname in ("Ewe/V", "<Ewe>/V", "Ecell/V", "<Ewe/V>", "<Ecell/V>"):
        return ("Ewe/V", np.float_)
    elif fieldname.endswith(
        (
            "/s",
            "/Hz",
            "/deg",
            "/W",
            "/mW",
            "/W.h",
            "/mW.h",
            "/A",
            "/mA",
            "/µA",
            "/A.h",
            "/mA.h",
            "/V",
            "/mV",
            "/F",
            "/mF",
            "/uF",
            "/µF",
            "/µF-2",
            "/nF",
            "/C",
            "/Ohm",
            "/Ohm-1",
            "/Ohm.cm",
            "/mS/cm",
            "/%",
            "/mol.L-1",
        )
    ):
        return (fieldname, np.float_)
    elif fieldname.startswith("Custom"):
        return (fieldname, np.float_)
    else:
        raise ValueError("Invalid column header: %s" % fieldname)


def comma_converter(float_text):
    """Convert text to float whether the decimal point is '.' or ','"""
    trans_table = bytes.maketrans(b",", b".")
    return float(float_text.translate(trans_table))


def MPTfile(file_or_path, encoding="ascii"):
    """Opens .mpt files as numpy record arrays

    Checks for the correct headings, skips any comments and returns a
    numpy record array object and a list of comments
    """

    if isinstance(file_or_path, str):
        mpt_file = open(file_or_path, "rb")
    else:
        mpt_file = file_or_path

    magic = next(mpt_file)
    if magic not in (b"EC-Lab ASCII FILE\r\n", b"BT-Lab ASCII FILE\r\n"):
        raise ValueError("Bad first line for EC-Lab file: '%s'" % magic)

    nb_headers_match = re.match(rb"Nb header lines : (\d+)\s*$", next(mpt_file))
    nb_headers = int(nb_headers_match.group(1))
    if nb_headers < 3:
        raise ValueError("Too few header lines: %d" % nb_headers)

    # The 'magic number' line, the 'Nb headers' line and the column headers
    # make three lines. Every additional line is a comment line.
    comments = [next(mpt_file) for i in range(nb_headers - 3)]

    fieldnames = next(mpt_file).decode(encoding).strip().split("\t")
    record_type = np.dtype(list(map(fieldname_to_dtype, fieldnames)))

    # Must be able to parse files where commas are used for decimal points
    converter_dict = dict(((i, comma_converter) for i in range(len(fieldnames))))
    mpt_array = np.loadtxt(mpt_file, dtype=record_type, converters=converter_dict)

    return mpt_array, comments


def MPTfileCSV(file_or_path):
    """Simple function to open MPT files as csv.DictReader objects

    Checks for the correct headings, skips any comments and returns a
    csv.DictReader object and a list of comments
    """

    if isinstance(file_or_path, str):
        mpt_file = open(file_or_path, "r")
    else:
        mpt_file = file_or_path

    magic = next(mpt_file)
    if magic.rstrip() != "EC-Lab ASCII FILE":
        raise ValueError("Bad first line for EC-Lab file: '%s'" % magic)

    nb_headers_match = re.match(r"Nb header lines : (\d+)\s*$", next(mpt_file))
    nb_headers = int(nb_headers_match.group(1))
    if nb_headers < 3:
        raise ValueError("Too few header lines: %d" % nb_headers)

    # The 'magic number' line, the 'Nb headers' line and the column headers
    # make three lines. Every additional line is a comment line.
    comments = [next(mpt_file) for i in range(nb_headers - 3)]

    mpt_csv = csv.DictReader(mpt_file, dialect="excel-tab")

    expected_fieldnames = (
        [
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
        ],
        [
            "mode",
            "ox/red",
            "error",
            "control changes",
            "Ns changes",
            "counter inc.",
            "time/s",
            "control/V",
            "Ewe/V",
            "dq/mA.h",
            "<I>/mA",
            "(Q-Qo)/mA.h",
            "x",
        ],
        [
            "mode",
            "ox/red",
            "error",
            "control changes",
            "Ns changes",
            "counter inc.",
            "time/s",
            "control/V",
            "Ewe/V",
            "I/mA",
            "dQ/mA.h",
            "P/W",
        ],
        [
            "mode",
            "ox/red",
            "error",
            "control changes",
            "Ns changes",
            "counter inc.",
            "time/s",
            "control/V",
            "Ewe/V",
            "<I>/mA",
            "dQ/mA.h",
            "P/W",
        ],
    )
    if mpt_csv.fieldnames not in expected_fieldnames:
        raise ValueError("Unrecognised headers for MPT file format")

    return mpt_csv, comments


VMPmodule_hdr_v1 = np.dtype(
    [
        ("shortname", "S10"),
        ("longname", "S25"),
        ("length", "<u4"),
        ("version", "<u4"),
        ("date", "S8"),
    ]
)

VMPmodule_hdr_v2 = np.dtype(
    [
        ("shortname", "S10"),
        ("longname", "S25"),
        ("max length", "<u4"),
        ("length", "<u4"),
        ("version", "<u4"),
        ("unknown2", "<u4"),  # 10 for set, log and loop, 11 for data
        ("date", "S8"),
    ]
)

# Column IDs specific to the "stack mode" used for BMS testing (specific to VMP3 ?)
stack_mode_colID_dtype_map = {
    103: ("Estack/V", "<f4"),
    163: ("|Estack|/V", "<f4"),
    211: ("E1/V", "<f4"),
    212: ("E2/V", "<f4"),
    213: ("E3/V", "<f4"),
    214: ("E4/V", "<f4"),
    215: ("E5/V", "<f4"),
    216: ("E6/V", "<f4"),
    217: ("E7/V", "<f4"),
    218: ("E8/V", "<f4"),
    219: ("E9/V", "<f4"),
    220: ("E10/V", "<f4"),
    241: ("|E1|/V", "<f4"),
    242: ("|E2|/V", "<f4"),
    243: ("|E3|/V", "<f4"),
    244: ("|E4|/V", "<f4"),
    245: ("|E5|/V", "<f4"),
    246: ("|E6|/V", "<f4"),
    247: ("|E7|/V", "<f4"),
    248: ("|E8|/V", "<f4"),
    249: ("|E9|/V", "<f4"),
    250: ("|E10|/V", "<f4"),
    271: ("Phase(Z1)/deg", "<f4"),
    272: ("Phase(Z2)/deg", "<f4"),
    273: ("Phase(Z3)/deg", "<f4"),
    274: ("Phase(Z4)/deg", "<f4"),
    275: ("Phase(Z5)/deg", "<f4"),
    276: ("Phase(Z6)/deg", "<f4"),
    277: ("Phase(Z7)/deg", "<f4"),
    278: ("Phase(Z8)/deg", "<f4"),
    279: ("Phase(Z9)/deg", "<f4"),
    280: ("Phase(Z10)/deg", "<f4"),
    301: ("|Z1|/Ohm", "<f4"),
    302: ("|Z2|/Ohm", "<f4"),
    303: ("|Z3|/Ohm", "<f4"),
    304: ("|Z4|/Ohm", "<f4"),
    305: ("|Z5|/Ohm", "<f4"),
    306: ("|Z6|/Ohm", "<f4"),
    307: ("|Z7|/Ohm", "<f4"),
    308: ("|Z8|/Ohm", "<f4"),
    309: ("|Z9|/Ohm", "<f4"),
    310: ("|Z10|/Ohm", "<f4"),
    331: ("Re(Z1)/Ohm", "<f4"),
    332: ("Re(Z2)/Ohm", "<f4"),
    333: ("Re(Z3)/Ohm", "<f4"),
    334: ("Re(Z4)/Ohm", "<f4"),
    335: ("Re(Z5)/Ohm", "<f4"),
    336: ("Re(Z6)/Ohm", "<f4"),
    337: ("Re(Z7)/Ohm", "<f4"),
    338: ("Re(Z8)/Ohm", "<f4"),
    339: ("Re(Z9)/Ohm", "<f4"),
    340: ("Re(Z10)/Ohm", "<f4"),
    361: ("-Im(Z1)/Ohm", "<f4"),
    362: ("-Im(Z2)/Ohm", "<f4"),
    363: ("-Im(Z3)/Ohm", "<f4"),
    364: ("-Im(Z4)/Ohm", "<f4"),
    365: ("-Im(Z5)/Ohm", "<f4"),
    366: ("-Im(Z6)/Ohm", "<f4"),
    367: ("-Im(Z7)/Ohm", "<f4"),
    368: ("-Im(Z8)/Ohm", "<f4"),
    369: ("-Im(Z9)/Ohm", "<f4"),
    370: ("-Im(Z10)/Ohm", "<f4"),
    391: ("<E1>/V", "<f4"),
    392: ("<E2>/V", "<f4"),
    393: ("<E3>/V", "<f4"),
    394: ("<E4>/V", "<f4"),
    395: ("<E5>/V", "<f4"),
    396: ("<E6>/V", "<f4"),
    397: ("<E7>/V", "<f4"),
    398: ("<E8>/V", "<f4"),
    399: ("<E9>/V", "<f4"),
    400: ("<E10>/V", "<f4"),
    422: ("Phase(Zstack)/deg", "<f4"),
    423: ("|Zstack|/Ohm", "<f4"),
    424: ("Re(Zstack)/Ohm", "<f4"),
    425: ("-Im(Zstack)/Ohm", "<f4"),
    426: ("<Estack>/V", "<f4"),
}

# Maps from colID to a tuple defining a numpy dtype
VMPdata_colID_dtype_map = {
    4: ("time/s", "<f8"),
    5: ("control/V/mA", "<f4"),
    6: ("Ewe/V", "<f4"),
    7: ("dq/mA.h", "<f8"),
    8: ("I/mA", "<f4"),
    9: ("Ece/V", "<f4"),
    11: ("<I>/mA", "<f8"),
    13: ("(Q-Qo)/mA.h", "<f8"),
    16: ("Analog IN 1/V", "<f4"),
    17: ("Analog IN 2/V", "<f4"),
    19: ("control/V", "<f4"),
    20: ("control/mA", "<f4"),
    23: ("dQ/mA.h", "<f8"),  # Same as (Q-Qo)/mA.h
    24: ("cycle number", "<f8"),
    26: ("Rapp/Ohm", "<f4"),
    27: ("Ewe-Ece/V", "<f4"),
    32: ("freq/Hz", "<f4"),
    33: ("|Ewe|/V", "<f4"),
    34: ("|I|/A", "<f4"),
    35: ("Phase(Z)/deg", "<f4"),
    36: ("|Z|/Ohm", "<f4"),
    37: ("Re(Z)/Ohm", "<f4"),
    38: ("-Im(Z)/Ohm", "<f4"),
    39: ("I Range", "<u2"),
    50: ("E0/V", "<f4"),
    69: ("R/Ohm", "<f4"),
    70: ("P/W", "<f4"),
    73: ("rotation rate/rpm", "<f4"),
    74: ("|Energy|/W.h", "<f8"),
    75: ("Analog OUT/V", "<f4"),
    76: ("<I>/mA", "<f4"),
    77: ("<Ewe>/V", "<f4"),
    78: ("Cs-2/µF-2", "<f4"),
    80: ("Rp/Ohm", "<f4"),
    86: ("Unk1", "<f4"),
    96: ("|Ece|/V", "<f4"),
    97: ("|Ice|/A", "<f4"),
    98: ("Phase(Zce)/deg", "<f4"),
    99: ("|Zce|/Ohm", "<f4"),
    100: ("Re(Zce)/Ohm", "<f4"),
    101: ("-Im(Zce)/Ohm", "<f4"),
    102: ("Cce-2/µF-2", "<f4"),
    123: ("Energy charge/W.h", "<f8"),
    124: ("Energy discharge/W.h", "<f8"),
    125: ("Capacitance charge/µF", "<f8"),
    126: ("Capacitance discharge/µF", "<f8"),
    131: ("Ns", "<u2"),
    134: ("Custom01", "<f4"),
    135: ("Custom02", "<f4"),
    136: ("Custom03", "<f4"),
    137: ("Custom04", "<f4"),
    138: ("Custom05", "<f4"),
    139: ("Custom06", "<f4"),
    140: ("Custom07", "<f4"),
    141: ("Custom08", "<f4"),
    168: ("Rcmp/Ohm", "<f4"),
    169: ("Cs/µF", "<f4"),
    170: ("sin ampl/V", "<f4"),
    172: ("Cp/µF", "<f4"),
    173: ("Cp-2/µF-2", "<f4"),
    174: ("<Ewe>/V", "<f4"),
    178: ("(Q-Qo)/C", "<f4"),
    179: ("dQ/C", "<f4"),  # Same as (Q-Qo)/C
    182: ("step time/s", "<f8"),
    185: ("<Ece>/V", "<f4"),
    196: ("If/mA", "<f4"),
    197: ("Ic/mA", "<f4"),
    198: ("CA/mol.L-1", "<f4"),
    199: ("CB/mol.L-1", "<f4"),
    209: ("pad number", "<f8"),
    211: ("Q charge/discharge/mA.h", "<f8"),
    212: ("half cycle", "<u4"),
    213: ("z cycle", "<u4"),
    217: ("THD Ewe/%", "<f4"),
    218: ("THD I/%", "<f4"),
    220: ("NSD Ewe/%", "<f4"),
    221: ("NSD I/%", "<f4"),
    223: ("NSR Ewe/%", "<f4"),
    224: ("NSR I/%", "<f4"),
    230: ("|Ewe h2|/V", "<f4"),
    231: ("|Ewe h3|/V", "<f4"),
    232: ("|Ewe h4|/V", "<f4"),
    233: ("|Ewe h5|/V", "<f4"),
    234: ("|Ewe h6|/V", "<f4"),
    235: ("|Ewe h7|/V", "<f4"),
    236: ("|I h2|/A", "<f4"),
    237: ("|I h3|/A", "<f4"),
    238: ("|I h4|/A", "<f4"),
    239: ("|I h5|/A", "<f4"),
    240: ("|I h6|/A", "<f4"),
    241: ("|I h7|/A", "<f4"),
    430: ("Phase(Zwe-ce)/deg", "<f4"),
    431: ("|Zwe-ce|/Ohm", "<f4"),
    432: ("Re(Zwe-ce)/Ohm", "<f4"),
    433: ("-Im(Zwe-ce)/Ohm", "<f4"),
    434: ("(Q-Qo)/C", "<f4"),
    435: ("dQ/C", "<f4"),
    436: ("Ece dc/V", "<f4"),
    438: ("step time/s", "<f8"),
    441: ("<Ece>/V", "<f4"),
    444: ("control disk/V", "<f4"),
    446: ("Edisk/V", "<f4"),
    448: ("Idisk/mA", "<f4"),
    450: ("(Q-Qo)disk/C", "<f8"),
    451: ("cycle number", "<f8"),
    452: ("control ring/V", "<f4"),
    453: ("Ering/V", "<f4"),
    454: ("Iring/mA", "<f4"),
    455: ("(Q-Qo)ring/C", "<f8"),
    462: ("Temperature/°C", "<f4"),
    467: ("Q charge/discharge/mA.h", "<f8"),
    468: ("half cycle", "<u4"),
    469: ("z cycle", "<u4"),
    471: ("<Ece>/V", "<f4"),
    473: ("THD Ewe/%", "<f4"),
    474: ("THD I/%", "<f4"),
    475: ("THD Ece/%", "<f4"),
    476: ("NSD Ewe/%", "<f4"),
    477: ("NSD I/%", "<f4"),
    478: ("NSD Ece/%", "<f4"),
    479: ("NSR Ewe/%", "<f4"),
    480: ("NSR I/%", "<f4"),
    481: ("NSR Ece/%", "<f4"),
    486: ("|Ewe h2|/V", "<f4"),
    487: ("|Ewe h3|/V", "<f4"),
    488: ("|Ewe h4|/V", "<f4"),
    489: ("|Ewe h5|/V", "<f4"),
    490: ("|Ewe h6|/V", "<f4"),
    491: ("|Ewe h7|/V", "<f4"),
    492: ("|I h2|/A", "<f4"),
    493: ("|I h3|/A", "<f4"),
    494: ("|I h4|/A", "<f4"),
    495: ("|I h5|/A", "<f4"),
    496: ("|I h6|/A", "<f4"),
    497: ("|I h7|/A", "<f4"),
    498: ("|Ece h2|/V", "<f4"),
    499: ("|Ece h3|/V", "<f4"),
    500: ("|Ece h4|/V", "<f4"),
    501: ("|Ece h5|/V", "<f4"),
    502: ("|Ece h6|/V", "<f4"),
    503: ("|Ece h7|/V", "<f4"),
    505: ("Rdc/Ohm", "<f4"),
    509: ("Acir/Dcir Control", "<u1"),
}

# These column IDs define flags which are all stored packed in a single byte
# The values in the map are (name, bitmask, dtype)
VMPdata_colID_flag_map = {
    1: ("mode", 0x03, np.uint8),
    2: ("ox/red", 0x04, np.bool_),
    3: ("error", 0x08, np.bool_),
    21: ("control changes", 0x10, np.bool_),
    31: ("Ns changes", 0x20, np.bool_),
    65: ("counter inc.", 0x80, np.bool_),
}


def parse_BioLogic_date(date_text):
    """Parse a date from one of the various formats used by Bio-Logic files."""
    date_formats = ["%m/%d/%y", "%m-%d-%y", "%m.%d.%y"]
    if isinstance(date_text, bytes):
        date_string = date_text.decode("ascii")
    else:
        date_string = date_text
    for date_format in date_formats:
        try:
            tm = time.strptime(date_string, date_format)
        except ValueError:
            continue
        else:
            break
    else:
        raise ValueError(
            f"Could not parse timestamp {date_string!r}" f" with any of the formats {date_formats}"
        )
    return date(tm.tm_year, tm.tm_mon, tm.tm_mday)


def VMPdata_dtype_from_colIDs(colIDs):
    """Get a numpy record type from a list of column ID numbers.

    The binary layout of the data in the MPR file is described by the sequence
    of column ID numbers in the file header. This function converts that
    sequence into a numpy dtype which can then be used to load data from the
    file with np.frombuffer().

    Some column IDs refer to small values which are packed into a single byte.
    The second return value is a dict describing the bit masks with which to
    extract these columns from the flags byte.

    """
    dtype_map = VMPdata_colID_dtype_map.copy()
    # If we detect a key corresponding to the stack mode, we load the specific colIDs
    if 103 in colIDs or 424 in colIDs:
        for key, value in stack_mode_colID_dtype_map.items():
            dtype_map[key] = value

    type_list = []
    field_name_counts = defaultdict(int)
    flags_dict = OrderedDict()
    for colID in colIDs:
        if colID in VMPdata_colID_flag_map:
            # Some column IDs represent boolean flags or small integers
            # These are all packed into a single 'flags' byte whose position
            # in the overall record is determined by the position of the first
            # column ID of flag type. If there are several flags present,
            # there is still only one 'flags' int
            if "flags" not in field_name_counts:
                type_list.append(("flags", "u1"))
                field_name_counts["flags"] = 1
            flag_name, flag_mask, flag_type = VMPdata_colID_flag_map[colID]
            # TODO what happens if a flag colID has already been seen
            # i.e. if flag_name is already present in flags_dict?
            # Does it create a second 'flags' byte in the record?
            flags_dict[flag_name] = (np.uint8(flag_mask), flag_type)
        elif colID in dtype_map:
            field_name, field_type = dtype_map[colID]
            field_name_counts[field_name] += 1
            count = field_name_counts[field_name]
            if count > 1:
                unique_field_name = "%s %d" % (field_name, count)
            else:
                unique_field_name = field_name
            type_list.append((unique_field_name, field_type))
        else:
            if type_list:
                raise NotImplementedError(
                    "Column ID {cid} after column {prev} "
                    "is unknown".format(cid=colID, prev=type_list[-1][0])
                )
            else:
                raise NotImplementedError(
                    "First column ID {cid} is unknown".format(cid=colID)
                )
    return np.dtype(type_list), flags_dict


def read_VMP_modules(fileobj, read_module_data=True):
    """Reads in module headers in the VMPmodule_hdr format. Yields a dict with
    the headers and offset for each module.

    N.B. the offset yielded is the offset to the start of the data i.e. after
    the end of the header. The data runs from (offset) to (offset+length)"""
    while True:
        module_magic = fileobj.read(len(b"MODULE"))
        if len(module_magic) == 0:  # end of file
            break
        elif module_magic != b"MODULE":
            if isinstance(file_or_path, str):
                fileobj.close()
            raise ValueError("Found %r, expecting start of new VMP MODULE" % module_magic)
        VMPmodule_hdr = VMPmodule_hdr_v1

        # Reading headers binary information
        hdr_bytes = fileobj.read(VMPmodule_hdr.itemsize)
        if len(hdr_bytes) < VMPmodule_hdr.itemsize:
            if isinstance(file_or_path, str):
                fileobj.close()
            raise IOError("Unexpected end of file while reading module header")

        # Checking if EC-Lab version is >= 11.50
        if hdr_bytes[35:39] == b"\xff\xff\xff\xff":
            VMPmodule_hdr = VMPmodule_hdr_v2
            hdr_bytes += fileobj.read(VMPmodule_hdr_v2.itemsize - VMPmodule_hdr_v1.itemsize)

        hdr = np.frombuffer(hdr_bytes, dtype=VMPmodule_hdr, count=1)
        hdr_dict = dict(((n, hdr[n][0]) for n in VMPmodule_hdr.names))
        hdr_dict["offset"] = fileobj.tell()
        if read_module_data:
            hdr_dict["data"] = fileobj.read(hdr_dict["length"])
            if len(hdr_dict["data"]) != hdr_dict["length"]:
                if isinstance(file_or_path, str):
                    fileobj.close()
                raise IOError(
                    """Unexpected end of file while reading data
                    current module: %s
                    length read: %d
                    length expected: %d"""
                    % (
                        hdr_dict["longname"],
                        len(hdr_dict["data"]),
                        hdr_dict["length"],
                    )
                )
            yield hdr_dict
        else:
            yield hdr_dict
            fileobj.seek(hdr_dict["offset"] + hdr_dict["length"], SEEK_SET)

def loop_from_file(file: str, encoding: str ="latin1"):
    """
    When an experiment is still running and it includes loops, 
    a _LOOP.txt file is temporarily created to progressively store the indexes of new loops.
    This function reads the file and creates the loop_index array for MPRfile initialization

    Parameters
    ----------
    file : str
        Path of the loop file.
    encoding : str, optional
        Encoding of the text file. The default is "latin1".

    Raises
    ------
    ValueError
        If the file does not start with "VMP EXPERIMENT LOOP INDEXES".

    Returns
    -------
    loop_index : np.array
        Indexes of data points that start a new loop.

    """
    with open(file, "r", encoding=encoding) as f:
        line = f.readline().strip()
        if line != LOOP_MAGIC:
            raise ValueError("Invalid magic for LOOP.txt file")
        loop_index = np.array([int(line) for line in f], dtype="u4")

    return loop_index


def timestamp_from_file(file: str, encoding: str ="latin1"):
    """
    When an experiment is still running, a .mpl file is temporarily created to store information 
    that will be added in the log module and will be appended to the data module in the .mpr file at the end of experiment 
    This function reads the file and extracts the experimental starting date and time as a timestamp for MPRfile initialization

    Parameters
    ----------
    file : str
        Path of the log file.
    encoding : str, optional
        Encoding of the text file. The default is "latin1".

    Raises
    ------
    ValueError
        If the file does not start with "EC-Lab LOG FILE" or "BT-Lab LOG FILE".

    Returns
    -------
    timestamp
        Date and time of the start of data acquisition
    """
    with open(file, "r", encoding=encoding) as f:
        line = f.readline().strip()
        if line not in LOG_MAGIC:
            raise ValueError("Invalid magic for .mpl file")
        log = f.read()
    start = tuple(
        map(
            int,
            re.findall(
                r"Acquisition started on : (\d+)\/(\d+)\/(\d+) (\d+):(\d+):(\d+)\.(\d+)",
                "".join(log),
            )[0],
        )
    )
    return datetime(
        int(start[2]), start[0], start[1], start[3], start[4], start[5], start[6] * 1000
    )


LOG_MAGIC = "EC-Lab LOG FILEBT-Lab LOG FILE"
LOOP_MAGIC = "VMP EXPERIMENT LOOP INDEXES"
MPR_MAGIC = b"BIO-LOGIC MODULAR FILE\x1a".ljust(48) + b"\x00\x00\x00\x00"


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
        self.loop_index = None
        self.startdate = None
        self.enddate = None
        self.timestamp = None
        if isinstance(file_or_path, str):
            mpr_file = open(file_or_path, "rb")
            loop_file = file_or_path[:-4] + "_LOOP.txt"  # loop file for running experiment
            log_file = file_or_path[:-1] + "l"  # log file for runnning experiment
        else:
            mpr_file = file_or_path
        magic = mpr_file.read(len(MPR_MAGIC))
        if magic != MPR_MAGIC:
            if isinstance(file_or_path, str):
                mpr_file.close()
            raise ValueError("Invalid magic for .mpr file: %s" % magic)

        modules = list(read_VMP_modules(mpr_file))
        if isinstance(file_or_path, str):
            mpr_file.close()

        self.modules = modules
        maybe_set_module = [m for m in modules if m["shortname"] == b"VMP Set   "]
        (data_module,) = (m for m in modules if m["shortname"] == b"VMP data  ")
        maybe_loop_module = [m for m in modules if m["shortname"] == b"VMP loop  "]
        maybe_log_module = [m for m in modules if m["shortname"] == b"VMP LOG   "]

        n_data_points = np.frombuffer(data_module["data"][:4], dtype="<u4")
        n_columns = np.frombuffer(data_module["data"][4:5], dtype="u1").item()

        if data_module["version"] == 0:
            # If EC-Lab version >= 11.50, column_types is [0 1 0 3 0 174...] instead of [1 3 174...]
            if np.frombuffer(data_module["data"][5:6], dtype="u1").item():
                column_types = np.frombuffer(data_module["data"][5:], dtype="u1", count=n_columns)
                remaining_headers = data_module["data"][5 + n_columns : 100]
                main_data = data_module["data"][100:]
            else:
                column_types = np.frombuffer(
                    data_module["data"][5:], dtype="u1", count=n_columns * 2
                )
                column_types = column_types[1::2]  # suppressing zeros in column types array
                # remaining headers should be empty except for bytes 5 + n_columns * 2
                # and 1006 which are sometimes == 1
                remaining_headers = data_module["data"][6 + n_columns * 2 : 1006]
                main_data = data_module["data"][1007:]
        elif data_module["version"] in [2, 3]:
            column_types = np.frombuffer(data_module["data"][5:], dtype="<u2", count=n_columns)
            # There are bytes of data before the main array starts
            if data_module["version"] == 3:
                num_bytes_before = 406  # version 3 added `\x01` to the start
            else:
                num_bytes_before = 405
            remaining_headers = data_module["data"][5 + 2 * n_columns : 405]
            main_data = data_module["data"][num_bytes_before:]
        elif data_module["version"] == 1:
            column_types = np.frombuffer(data_module["data"][5:], dtype="<u2", count=n_columns)
            # There are bytes of data before the main array starts
            num_bytes_before = 195
            remaining_headers = data_module["data"][5 + 2 * n_columns : num_bytes_before]
            main_data = data_module["data"][num_bytes_before:]
        else:
            raise ValueError("Unrecognised version for data module: %d" % data_module["version"])

        assert not any(remaining_headers)

        self.dtype, self.flags_dict = VMPdata_dtype_from_colIDs(column_types)
        self.data = np.frombuffer(main_data, dtype=self.dtype)
        assert self.data.shape[0] == n_data_points

        # No idea what these 'column types' mean or even if they are actually
        # column types at all
        self.version = int(data_module["version"])
        self.cols = column_types
        self.npts = n_data_points
        if maybe_set_module:
            (set_module,) = maybe_set_module
            self.startdate = parse_BioLogic_date(set_module["date"])

        if maybe_loop_module:
            (loop_module,) = maybe_loop_module
            if loop_module["version"] == 0:
                self.loop_index = np.frombuffer(loop_module["data"][4:], dtype="<u4")
                self.loop_index = np.trim_zeros(self.loop_index, "b")
            else:
                raise ValueError(
                    "Unrecognised version for data module: %d" % data_module["version"]
                )
        else:
            if path.isfile(loop_file):
                self.loop_index = loop_from_file(loop_file)
                if self.loop_index[-1] < n_data_points:
                    self.loop_index = np.append(self.loop_index, n_data_points)

        if maybe_log_module:
            (log_module,) = maybe_log_module
            self.enddate = parse_BioLogic_date(log_module["date"])

            for i in range(8):
                log_buff = np.frombuffer(log_module["data"][400 + i :], dtype="<f8", count=37)
                ole_timestamp = log_buff[(log_buff > 33315) & (log_buff < 50000)]
                if ole_timestamp.size > 0:
                    break
            if ole_timestamp.size == 0:
                raise ValueError("Could not find timestamp in the LOG module")

            ole_base = datetime(1899, 12, 30, tzinfo=None)
            ole_timedelta = timedelta(days=ole_timestamp[0])
            self.timestamp = ole_base + ole_timedelta
            if self.startdate is None:
                self.startdate = self.timestamp.date()
            elif self.startdate != self.timestamp.date():
                raise ValueError(
                    "Date mismatch:\n"
                    + "    Start date: %s\n" % self.startdate
                    + "    End date: %s\n" % self.enddate
                    + "    Timestamp: %s\n" % self.timestamp
                )
        else:
            if path.isfile(log_file):
                self.timestamp = timestamp_from_file(log_file)

    def get_flag(self, flagname):
        if flagname in self.flags_dict:
            mask, dtype = self.flags_dict[flagname]
            return np.array(self.data["flags"] & mask, dtype=dtype)
        else:
            raise AttributeError("Flag '%s' not present" % flagname)
