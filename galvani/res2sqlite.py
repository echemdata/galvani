#!/usr/bin/python

import subprocess as sp
import sqlite3
import re
import csv
import argparse


# The following scripts are adapted from the result of running
# $ mdb-schema <result.res> oracle

mdb_tables = [
    'Version_Table',
    'Global_Table',
    'Resume_Table',
    'Channel_Normal_Table',
    'Channel_Statistic_Table',
    'Auxiliary_Table',
    'Event_Table',
    'Smart_Battery_Info_Table',
    'Smart_Battery_Data_Table',
]
mdb_5_23_tables = [
    'MCell_Aci_Data_Table',
    'Aux_Global_Data_Table',
    'Smart_Battery_Clock_Stretch_Table',
]

mdb_tables_text = {
    'Version_Table',
    'Global_Table',
    'Event_Table',
    'Smart_Battery_Info_Table',
}
mdb_tables_numeric = {
    'Resume_Table',
    'Channel_Normal_Table',
    'Channel_Statistic_Table',
    'Auxiliary_Table',
    'Smart_Battery_Data_Table',
    'MCell_Aci_Data_Table',
    'Aux_Global_Data_Table',
    'Smart_Battery_Clock_Stretch_Table',
}

mdb_create_scripts = {
    "Version_Table": """
CREATE TABLE Version_Table
 (
    Version_Schema_Field    TEXT,
    Version_Comments_Field  TEXT
); """,
    "Global_Table": """
CREATE TABLE Global_Table
 (
    Test_ID                         INTEGER PRIMARY KEY,
    Test_Name                       TEXT,
    Channel_Index                   INTEGER,
    Start_DateTime                  REAL,
    DAQ_Index                       INTEGER,
    Channel_Type                    INTEGER,
    Creator                         TEXT,
    Comments                        TEXT,
    Schedule_File_Name              TEXT,
    Channel_Number                  INTEGER,
    Mapped_Aux_Voltage_Number       INTEGER,
    Mapped_Aux_Temperature_Number   INTEGER,
    Mapped_Aux_Pressure_Number      INTEGER,
    Mapped_Aux_PH_Number            INTEGER,
    Mapped_Aux_Flow_Rate_CNumber    INTEGER,
    Applications_Path               TEXT,
    Log_ChanStat_Data_Flag          INTEGER,
    Log_Aux_Data_Flag               INTEGER,
    Log_Event_Data_Flag             INTEGER,
    Log_Smart_Battery_Data_Flag     INTEGER,
  -- The following items are in 5.26 but not in 5.23
    Log_Can_BMS_Data_Flag           INTEGER DEFAULT NULL,
    Software_Version                TEXT DEFAULT NULL,
    Serial_Number                   TEXT DEFAULT NULL,
    Schedule_Version                TEXT DEFAULT NULL,
    MASS                            REAL DEFAULT NULL,
    Specific_Capacity               REAL DEFAULT NULL,
    Capacity                        REAL DEFAULT NULL,
  -- Item_ID exists in all versions
    Item_ID                         TEXT,
  -- These items are in 5.26 and 5.23 but not in 1.14
    Mapped_Aux_Conc_CNumber         INTEGER DEFAULT NULL,
    Mapped_Aux_DI_CNumber           INTEGER DEFAULT NULL,
    Mapped_Aux_DO_CNumber           INTEGER DEFAULT NULL
); """,
    "Resume_Table": """
CREATE TABLE Resume_Table
 (
    Test_ID         INTEGER REFERENCES Global_Table(Test_ID),
    Step_Index      INTEGER,
    Cycle_Index     INTEGER,
    Channel_Status  INTEGER,
    Test_Time       REAL,
    Step_Time       REAL,
    CCapacity       REAL,
    DCapacity       REAL,
    CEnergy         REAL,
    DEnergy         REAL,
    TC_Time1        REAL,
    TC_Time2        REAL,
    TC_Time3        REAL,
    TC_Time4        REAL,
    TC_CCapacity1   REAL,
    TC_CCapacity2   REAL,
    TC_DCapacity1   REAL,
    TC_DCapacity2   REAL,
    TC_CEnergy1     REAL,
    TC_CEnergy2     REAL,
    TC_DEnergy1     REAL,
    TC_DEnergy2     REAL,
    MV_Counter1     REAL,
    MV_Counter2     REAL,
    MV_Counter3     REAL,
    MV_Counter4     REAL,
  -- Version 1.14 ends here, version 5.23 continues
    Charge_Time     REAL DEFAULT NULL,
    Discharge_Time  REAL DEFAULT NULL
); """,
    "Channel_Normal_Table": """
CREATE TABLE Channel_Normal_Table
 (
    Test_ID                 INTEGER REFERENCES Global_Table(Test_ID),
    Data_Point              INTEGER,
    Test_Time               REAL,
    Step_Time               REAL,
    DateTime                REAL,
    Step_Index              INTEGER,
    Cycle_Index             INTEGER,
    Is_FC_Data              INTEGER,
    Current                 REAL,
    Voltage                 REAL,
    Charge_Capacity         REAL,
    Discharge_Capacity      REAL,
    Charge_Energy           REAL,
    Discharge_Energy        REAL,
    "dV/dt"                 REAL,
    Internal_Resistance     REAL,
    AC_Impedance            REAL,
    ACI_Phase_Angle         REAL
); """,
    "Channel_Statistic_Table": """
CREATE TABLE Channel_Statistic_Table
 (
    Test_ID                 INTEGER,
    Data_Point              INTEGER,
    Vmax_On_Cycle           REAL,
  -- Version 1.14 ends here, version 5.23 continues
    Charge_Time             REAL DEFAULT NULL,
    Discharge_Time          REAL DEFAULT NULL,
    FOREIGN KEY (Test_ID, Data_Point)
        REFERENCES Channel_Normal_Table (Test_ID, Data_Point)
); """,
    "Auxiliary_Table": """
CREATE TABLE Auxiliary_Table
 (
    Test_ID                 INTEGER,
    Data_Point              INTEGER,
    Auxiliary_Index         INTEGER,
    Data_Type               INTEGER,
    X                       REAL,
    "dX/dt"                 REAL,
    FOREIGN KEY (Test_ID, Data_Point)
        REFERENCES Channel_Normal_Table (Test_ID, Data_Point)
); """,
    "Event_Table": """
CREATE TABLE Event_Table
 (
    Test_ID                 INTEGER REFERENCES Global_Table(Test_ID),
    DateTime                REAL,
    Test_Time               REAL,
    Event_Type              INTEGER,
    Event_Describe          TEXT
); """,
    "Smart_Battery_Info_Table":  """
CREATE TABLE Smart_Battery_Info_Table
 (
    Test_ID                 INTEGER REFERENCES Global_Table(Test_ID),
    ManufacturerDate        REAL,
    ManufacturerAccess      TEXT,
    SpecificationInfo       TEXT,
    FullChargeCapacity      REAL,
    ChargingCurrent         REAL,
    ChargingVoltage         REAL,
    DesignCapacity          REAL,
    DesignVoltage           REAL,
    SerialNumber            INTEGER,
    ManufacturerName        TEXT,
    DeviceName              TEXT,
    DeviceChemistry         TEXT,
    ManufacturerData        TEXT,
  -- Version 1.14 ends here, version 5.23 continues
    Frequency               INTEGER DEFAULT NULL
); """,
    "Smart_Battery_Data_Table": """
CREATE TABLE Smart_Battery_Data_Table
 (
    Test_ID                 INTEGER,
    Data_Point              INTEGER,
    RemainingCapacityAlarm  REAL,
    RemainingTimeAlarm      INTEGER,
    BatteryMode             INTEGER,
    AtRate                  REAL,
    AtRateTimeToFull        INTEGER,
    AtRateTimeToEmpty       INTEGER,
    AtRateOK                INTEGER,
    Temperature             REAL,
    Voltage                 REAL,
    Current                 REAL,
    AverageCurrent          REAL,
    MaxError                INTEGER,
    RelativeStateOfCharge   INTEGER,
    AbsoluteStateOfCharge   INTEGER,
    RemainingCapacity       REAL,
    RunTimeToEmpty          INTEGER,
    AverageTimeToEmpty      INTEGER,
    AverageTimeToFull       INTEGER,
    BatteryStatus           INTEGER,
    CycleCount              INTEGER,
  -- Version 1.14 ends here, version 5.23 continues
    Pack_Status             INTEGER DEFAULT NULL,
    Pack_Configuration      INTEGER DEFAULT NULL,
    VCELL4                  REAL DEFAULT NULL,
    VCELL3                  REAL DEFAULT NULL,
    VCELL2                  REAL DEFAULT NULL,
    VCELL1                  REAL DEFAULT NULL,
    ManufacturerAccess      TEXT DEFAULT NULL,
    FullChargeCapacity      REAL DEFAULT NULL,
    BroadCast               INTEGER DEFAULT NULL,
    GPIO1                   INTEGER DEFAULT NULL,
    GPIO2                   INTEGER DEFAULT NULL,
    OptVCELL4               REAL DEFAULT NULL,
    OptVCELL3               REAL DEFAULT NULL,
    OptVCELL2               REAL DEFAULT NULL,
    OptVCELL1               REAL DEFAULT NULL,
    OMF1                    INTEGER DEFAULT NULL,
    OMF2                    INTEGER DEFAULT NULL,
    OMF3                    INTEGER DEFAULT NULL,
    OMF4                    INTEGER DEFAULT NULL,
    OMF5                    INTEGER DEFAULT NULL,
    FTEMP                   INTEGER DEFAULT NULL,
    STATUS                  INTEGER DEFAULT NULL,
    FET_TEMP                INTEGER DEFAULT NULL,
    ChargingCurrent         REAL DEFAULT NULL,
    ChargingVoltage         REAL DEFAULT NULL,
    ManufacturerData        REAL DEFAULT NULL,
  -- Version 5.23 ends here, version 5.26 continues
    BATMAN_Status           INTEGER DEFAULT NULL, 
    DTM_PDM_Status          INTEGER DEFAULT NULL, 

    FOREIGN KEY (Test_ID, Data_Point)
        REFERENCES Channel_Normal_Table (Test_ID, Data_Point)
); """,
    # The following tables are not present in version 1.14
    'MCell_Aci_Data_Table': """
CREATE TABLE MCell_Aci_Data_Table
 (
    Test_ID			INTEGER,
    Data_Point		INTEGER,
    Cell_Index		INTEGER,
    ACI			REAL,
    Phase_Shift		REAL,
    Voltage			REAL,
    Current			REAL,
    FOREIGN KEY (Test_ID, Data_Point)
        REFERENCES Channel_Normal_Table (Test_ID, Data_Point)
);""",
    'Aux_Global_Data_Table': """
CREATE TABLE Aux_Global_Data_Table
 (
    Channel_Index		INTEGER,
    Auxiliary_Index	INTEGER,
    Data_Type		INTEGER,
    Nickname		TEXT,
    Unit			TEXT
);""",
    'Smart_Battery_Clock_Stretch_Table': """
CREATE TABLE Smart_Battery_Clock_Stretch_Table
 (
    Test_ID			    INTEGER,
    Data_Point		    INTEGER,
    ManufacturerAccess	    INTEGER,
    RemainingCapacityAlarm INTEGER,
    RemainingTimeAlarm	    INTEGER,
    BatteryMode		    INTEGER,
    AtRate			    INTEGER,
    AtRateTimeToFull	    INTEGER,
    AtRateTimeToEmpty	    INTEGER,
    AtRateOK		    INTEGER,
    Temperature		    INTEGER,
    Voltage			    INTEGER,
    Current			    INTEGER,
    AverageCurrent         INTEGER,
    MaxError		    INTEGER,
    RelativeStateOfCharge  INTEGER,
    AbsoluteStateOfCharge  INTEGER,
    RemainingCapacity	    INTEGER,
    FullChargeCapacity	    INTEGER,
    RunTimeToEmpty	    INTEGER,
    AverageTimeToEmpty	    INTEGER,
    AverageTimeToFull	    INTEGER,
    ChargingCurrent	    INTEGER,
    ChargingVoltage	    INTEGER,
    BatteryStatus		    INTEGER,
    CycleCount		    INTEGER,
    DesignCapacity	    INTEGER,
    DesignVoltage		    INTEGER,
    SpecificationInfo	    INTEGER,
    ManufacturerDate	    INTEGER,
    SerialNumber		    INTEGER,
    ManufacturerName	    INTEGER,
    DeviceName		    INTEGER,
    DeviceChemistry	    INTEGER,
    ManufacturerData	    INTEGER,
    Pack_Status		    INTEGER,
    Pack_Configuration	    INTEGER,
    VCELL4			    INTEGER,
    VCELL3			    INTEGER,
    VCELL2			    INTEGER,
    VCELL1			    INTEGER,
    FOREIGN KEY (Test_ID, Data_Point)
        REFERENCES Channel_Normal_Table (Test_ID, Data_Point)
);"""}

mdb_create_indices = {
    "Channel_Normal_Table": """
CREATE UNIQUE INDEX data_point_index ON Channel_Normal_Table (Test_ID, Data_Point);
CREATE INDEX voltage_index ON Channel_Normal_Table (Test_ID, Voltage);
CREATE INDEX test_time_index ON Channel_Normal_Table (Test_ID, Test_Time);
"""}

helper_table_script = """
CREATE TEMPORARY TABLE capacity_helper(
    Test_ID			    INTEGER NOT NULL,
    Cycle_Index		    INTEGER NOT NULL,
    Charge_Capacity        REAL NOT NULL,
    Discharge_Capacity     REAL NOT NULL,
    Charge_Energy          REAL NOT NULL,
    Discharge_Energy       REAL NOT NULL,
    FOREIGN KEY (Test_ID, Cycle_Index)
        REFERENCES Channel_Normal_Table (Test_ID, Cycle_Index)
);

INSERT INTO capacity_helper
    SELECT Test_ID, Cycle_Index,
           max(Charge_Capacity), max(Discharge_Capacity),
           max(Charge_Energy), max(Discharge_Energy)
        FROM Channel_Normal_Table
        GROUP BY Test_ID, Cycle_Index;

-- ## Alternative way of selecting ##
-- select *
--     from Channel_Normal_Table as a join Channel_Normal_Table as b
--         on (a.Test_ID = b.Test_ID and a.Data_Point = b.Data_Point + 1
--              and a.Charge_Capacity < b.Charge_Capacity);

DROP TABLE IF EXISTS Capacity_Sum_Table;
CREATE TABLE Capacity_Sum_Table(
    Test_ID			    INTEGER NOT NULL,
    Cycle_Index		    INTEGER NOT NULL,
    Charge_Capacity_Sum    REAL NOT NULL,
    Discharge_Capacity_Sum REAL NOT NULL,
    Charge_Energy_Sum      REAL NOT NULL,
    Discharge_Energy_Sum   REAL NOT NULL,
    FOREIGN KEY (Test_ID, Cycle_Index)
        REFERENCES Channel_Normal_Table (Test_ID, Cycle_Index)
);

INSERT INTO Capacity_Sum_Table
    SELECT a.Test_ID, a.Cycle_Index,
           total(b.Charge_Capacity), total(b.Discharge_Capacity),
           total(b.Charge_Energy), total(b.Discharge_Energy)
        FROM capacity_helper AS a LEFT JOIN capacity_helper AS b
            ON (a.Test_ID = b.Test_ID AND a.Cycle_Index > b.Cycle_Index)
        GROUP BY a.Test_ID, a.Cycle_Index;

DROP TABLE capacity_helper;

CREATE VIEW IF NOT EXISTS Capacity_View
    AS SELECT Test_ID, Data_Point, Test_Time, Step_Time, DateTime,
              Step_Index, Cycle_Index, Current, Voltage, "dV/dt",
              ( (Discharge_Capacity + Discharge_Capacity_Sum)
              - (Charge_Capacity + Charge_Capacity_Sum) ) AS Net_Capacity,
              ( (Discharge_Capacity + Discharge_Capacity_Sum)
              + (Charge_Capacity + Charge_Capacity_Sum) ) AS Gross_Capacity,
              ( (Discharge_Energy + Discharge_Energy_Sum)
              - (Charge_Energy + Charge_Energy_Sum) ) AS Net_Energy,
              ( (Discharge_Energy + Discharge_Energy_Sum)
              + (Charge_Energy + Charge_Energy_Sum) ) AS Gross_Energy
        FROM Channel_Normal_Table NATURAL JOIN Capacity_Sum_Table;
"""


def mdb_get_data_text(s3db, filename, table):
    print("Reading %s..." % table)
    insert_pattern = re.compile(
        r'INSERT INTO "\w+" \([^)]+?\) VALUES \(("[^"]*"|[^")])+?\);\n',
        re.IGNORECASE
    )
    try:
        # Initialize values to avoid NameError in except clause
        mdb_output = ''
        insert_match = None
        with sp.Popen(['mdb-export', '-I', 'postgres', filename, table],
                      bufsize=-1, stdin=sp.DEVNULL, stdout=sp.PIPE,
                      universal_newlines=True) as mdb_sql:

            mdb_output = mdb_sql.stdout.read()
            while len(mdb_output) > 0:
                insert_match = insert_pattern.match(mdb_output)
                s3db.execute(insert_match.group())
                mdb_output = mdb_output[insert_match.end():]
                mdb_output += mdb_sql.stdout.read()
            s3db.commit()

    except OSError as e:
        if e.errno == 2:
            raise RuntimeError('Could not locate the `mdb-export` executable. '
                               'Check that mdbtools is properly installed.')
        else:
            raise
    except BaseException:
        print("Error while importing %s" % table)
        if mdb_output:
            print("Remaining mdb-export output:", mdb_output)
        if insert_match:
            print("insert_re match:", insert_match)
        raise


def mdb_get_data_numeric(s3db, filename, table):
    print("Reading %s..." % table)
    try:
        with sp.Popen(['mdb-export', filename, table],
                      bufsize=-1, stdin=sp.DEVNULL, stdout=sp.PIPE,
                      universal_newlines=True) as mdb_sql:
            mdb_csv = csv.reader(mdb_sql.stdout)
            mdb_headers = next(mdb_csv)
            quoted_headers = ['"%s"' % h for h in mdb_headers]
            joined_headers = ', '.join(quoted_headers)
            joined_placemarks = ', '.join(['?' for h in mdb_headers])
            insert_stmt = 'INSERT INTO "{0}" ({1}) VALUES ({2});'.format(
                table,
                joined_headers,
                joined_placemarks,
            )
            s3db.executemany(insert_stmt, mdb_csv)
            s3db.commit()
    except OSError as e:
        if e.errno == 2:
            raise RuntimeError('Could not locate the `mdb-export` executable. '
                               'Check that mdbtools is properly installed.')
        else:
            raise


def mdb_get_data(s3db, filename, table):
    if table in mdb_tables_text:
        mdb_get_data_text(s3db, filename, table)
    elif table in mdb_tables_numeric:
        mdb_get_data_numeric(s3db, filename, table)
    else:
        raise ValueError("'%s' is in neither mdb_tables_text nor mdb_tables_numeric" % table)


def mdb_get_version(filename):
    """Get the version number from an Arbin .res file.

    Reads the Version_Table and parses the version from Version_Schema_Field.
    """
    print("Reading version number...")
    try:
        with sp.Popen(['mdb-export', filename, 'Version_Table'],
                      bufsize=-1, stdin=sp.DEVNULL, stdout=sp.PIPE,
                      universal_newlines=True) as mdb_sql:
            mdb_csv = csv.reader(mdb_sql.stdout)
            mdb_headers = next(mdb_csv)
            mdb_values = next(mdb_csv)
            try:
                next(mdb_csv)
            except StopIteration:
                pass
            else:
                raise ValueError('Version_Table of %s lists multiple versions' % filename)
    except OSError as e:
        if e.errno == 2:
            raise RuntimeError('Could not locate the `mdb-export` executable. '
                               'Check that mdbtools is properly installed.')
        else:
            raise
    if 'Version_Schema_Field' not in mdb_headers:
        raise ValueError('Version_Table of %s does not contain a Version_Schema_Field column'
                         % filename)
    version_fields = dict(zip(mdb_headers, mdb_values))
    version_text = version_fields['Version_Schema_Field']
    version_match = re.fullmatch('Results File ([.0-9]+)', version_text)
    if not version_match:
        raise ValueError('File version "%s" did not match expected format' % version_text)
    version_string = version_match.group(1)
    version_tuple = tuple(map(int, version_string.split('.')))
    return version_tuple


def convert_arbin_to_sqlite(input_file, output_file):
    """Read data from an Arbin .res data file and write to a sqlite file.

    Any data currently in the sqlite file will be erased!
    """
    arbin_version = mdb_get_version(input_file)

    s3db = sqlite3.connect(output_file)

    for table in reversed(mdb_tables + mdb_5_23_tables):
        s3db.execute('DROP TABLE IF EXISTS "%s";' % table)

    for table in mdb_tables:
        s3db.executescript(mdb_create_scripts[table])
        mdb_get_data(s3db, input_file, table)
        if table in mdb_create_indices:
            print("Creating indices for %s..." % table)
            s3db.executescript(mdb_create_indices[table])

    if arbin_version >= (5, 23):
        for table in mdb_5_23_tables:
            s3db.executescript(mdb_create_scripts[table])
            mdb_get_data(s3db, input_file, table)
            if table in mdb_create_indices:
                s3db.executescript(mdb_create_indices[table])

    print("Creating helper table for capacity and energy totals...")
    s3db.executescript(helper_table_script)

    print("Vacuuming database...")
    s3db.executescript("VACUUM; ANALYZE;")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert Arbin .res files to sqlite3 databases using mdb-export",
    )
    parser.add_argument('input_file', type=str)  # need file name to pass to sp.Popen
    parser.add_argument('output_file', type=str)  # need file name to pass to sqlite3.connect

    args = parser.parse_args(argv)
    convert_arbin_to_sqlite(args.input_file, args.output_file)


if __name__ == '__main__':
    main()
