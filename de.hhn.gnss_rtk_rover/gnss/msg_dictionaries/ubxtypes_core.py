"""
UBX Protocol core globals and constants
Created on 27 Sep 2020
Information sourced from u-blox Interface Specifications © 2013-2021, u-blox AG
Created on 4 Sep 2022
:author: vdueck

Based on:
:author: semuadmin
:copyright: SEMU Consulting © 2020
:license: BSD 3-Clause
"""

UBX_HDR = b"\xb5\x62"
NMEA_HDR = [b"\x24\x47", b"\x24\x50"]
GET = 0
SET = 1
POLL = 2
VALNONE = 0
VALCKSUM = 1
NMEA_PROTOCOL = 1
UBX_PROTOCOL = 2
RTCM3_PROTOCOL = 4
ERR_RAISE = 2
ERR_LOG = 1
ERR_IGNORE = 0

GNSSLIST = {
    0: "GPS",
    1: "SBAS",
    2: "Galileo",
    3: "BeiDou",
    4: "IMES",
    5: "QZSS",
    6: "GLONASS",
}

FIXTYPES = {
    0: "Invalid, no position available",
    1: "Autonomous GNSS fix, no correction data used",
    2: "DGNSS fix, using a local DGNSS base station or correction service",
    3: "PPS fix",
    4: "RTK fix, high accuracy Real Time Kinematic",
    5: "RTK Float, better than DGNSS, but not as accurate as RTK fix",
    6: "Estimated fix (dead reckoning)",
    7: "Manual input mode",
    8: "Simulation mode",
    9: "WAAS fix (not NMEA standard, but NotAvel receivers report this instead of a 2)"
}

# scaling factor constants
SCAL9 = 1e-9  # 0.000000001
SCAL8 = 1e-8  # 0.00000001
SCAL7 = 1e-7  # 0.0000001
SCAL6 = 1e-6  # 0.000001
SCAL5 = 1e-5  # 0.00001
SCAL4 = 1e-4  # 0.0001
SCAL3 = 1e-3  # 0.001
SCAL2 = 1e-2  # 0.01
SCAL1 = 1e-1  # 0.1
SCALROUND = 12  # number of dp to round scaled attributes to

# THESE ARE THE UBX PROTOCOL PAYLOAD ATTRIBUTE TYPES
A250 = "A250"  # Array of 250 bytes, parsed as U1[250]
A256 = "A256"  # Array of 256 bytes, parsed as U1[256]
C2 = "C002"  # ASCII / ISO 8859.1 Encoding 2 bytes
C6 = "C006"  # ASCII / ISO 8859.1 Encoding 6 bytes
C10 = "C010"  # ASCII / ISO 8859.1 Encoding 10 bytes
C30 = "C030"  # ASCII / ISO 8859.1 Encoding 30 bytes
C32 = "C032"  # ASCII / ISO 8859.1 Encoding 32 bytes
CH = "CH"  # ASCII / ISO 8859.1 Encoding Variable Length
E1 = "E001"  # Unsigned Int Enumeration 1 byte
E2 = "E002"  # Unsigned Int Enumeration 2 bytes
E4 = "E004"  # Unsigned Int Enumeration 4 bytes
I1 = "I001"  # Signed Int 2's complement 1 byte
I2 = "I002"  # Signed Int 2's complement 2 bytes
I4 = "I004"  # Signed Int 2's complement 4 bytes
I8 = "I008"  # Signed Int 2's complement 8 bytes
L = "L001"  # Boolean stored as U01
U1 = "U001"  # Unsigned Int 1 byte
U2 = "U002"  # Unsigned Int 2 bytes
U3 = "U003"  # Unsigned Int 3 bytes
U4 = "U004"  # Unsigned Int 4 bytes
U5 = "U005"  # Unsigned Int 5 bytes
U6 = "U006"  # Unsigned Int 6 bytes
U7 = "U007"  # Unsigned Int 7 bytes
U8 = "U008"  # Unsigned Int 8 bytes
U9 = "U009"  # Unsigned Int 9 bytes
U10 = "U010"  # Unsigned Int 10 bytes
U11 = "U011"  # Unsigned Int 11 bytes
U12 = "U012"  # Unsigned Int 12 bytes
U16 = "U016"  # Unsigned Int 16 bytes
U20 = "U020"  # Unsigned Int 20 bytes
U22 = "U022"  # Unsigned Int 22 bytes
U23 = "U023"  # Unsigned Int 23 bytes
U24 = "U024"  # Unsigned Int 24 bytes
U32 = "U032"  # Unsigned Int 32 bytes
U40 = "U040"  # Unsigned Int 40 bytes
U64 = "U064"  # Unsigned Int 64 bytes
X1 = "X001"  # Bitfield 1 byte
X2 = "X002"  # Bitfield 2 bytes
X4 = "X004"  # Bitfield 4 bytes
X6 = "X006"  # Bitfield 6 bytes
X8 = "X008"  # Bitfield 8 bytes
X24 = "X024"  # Bitfield 24 bytes
R4 = "R004"  # Float (IEEE 754) Single Precision 4 bytes
R8 = "R008"  # Float (IEEE 754) Double Precision 8 bytes

# THESE ARE THE UBX PROTOCOL CORE MESSAGE CLASSES
UBX_CLASSES = {
    b"\x01": "NAV",  # Navigation Results: Position, Speed, Time, Acc, Heading, DOP, SVs used
    b"\x02": "RXM",  # Receiver Manager Messages: Satellite Status, RTC Status
    b"\x04": "INF",  # Information Messages: Printf-Style Messages, with IDs such as Error, Warning, Notice
    b"\x05": "ACK",  # Ack/Nack Messages: as replies to CFG Input Messages
    b"\x06": "CFG",  # Configuration Input Messages: Set Dynamic Model, Set DOP Mask, Set Baud Rate, etc.
    b"\x09": "UPD",  # Firmware Update Messages: Memory/Flash erase/write, Reboot, Flash identification, etc.
    b"\x0a": "MON",  # Monitoring Messages: Communication Status, CPU Load, Stack Usage, Task Status
    b"\x0d": "TIM",  # Timing Messages: Timepulse Output, Timemark Results
    b"\x13": "MGA",  # Multiple GNSS Assistance Messages: Assistance data for various GNSS
    b"\x21": "LOG",  # Logging Messages: Log creation, deletion, info and retrieval
    b"\x27": "SEC",  # Security Feature Messages
    b"\x66": "FOO",  # Dummy message class for testing
}

# THESE ARE THE UBX PROTOCOL CORE MESSAGE IDENTITIES
# Payloads for each of these identities are defined in the ubxtypes_* modules
UBX_MSGIDS = {
    b"\x05\x01": "ACK-ACK",
    b"\x05\x00": "ACK-NAK",

    # Configuration messages
    b"\x06\x17": "CFG-NMEA",  # NB: 3 versions of this
    b"\x06\x08": "CFG-RATE",
    b"\x06\x01": "CFG-MSG",
    b"\x06\x8c": "CFG-VALDEL",
    b"\x06\x8b": "CFG-VALGET",
    b"\x06\x8a": "CFG-VALSET",

    # Navigation messages
    b"\x01\x07": "NAV-PVT",
    b"\x01\x35": "NAV-SAT",
    b"\x01\x43": "NAV-SIG",
    b"\x01\x03": "NAV-STATUS",
    b"\x01\x3b": "NAV-SVIN",

    # Firmware update messages
    b"\x09\x14": "UPD-SOS",

    # NMEA Standard message types
    # Used to poll message rates via CFG-MSG; not parsed by msg_dictionaries
    b"\xf0\x0a": "DTM",  # Datum Reference
    b"\xf0\x45": "GAQ",  # Poll Standard Message - Talker ID GA (Galileo)
    b"\xf0\x44": "GBQ",  # Poll Standard Message - Talker ID GB (BeiDou)
    b"\xf0\x09": "GBS",  # GNSS Satellite Fault Detection
    b"\xf0\x00": "GGA",  # Global positioning system fix data
    b"\xf0\x01": "GLL",  # Latitude and longitude, with time of position fix and status
    b"\xf0\x43": "GLQ",  # Poll Standard Message - Talker ID GL (GLONASS)
    b"\xf0\x42": "GNQ",  # Poll Standard Message - Talker ID GN (Any GNSS)
    b"\xf0\x0d": "GNS",  # GNSS Fix Data
    b"\xf0\x40": "GPQ",  # Poll Standard Message - Talker ID GP (GPS, SBAS)
    b"\xf0\x47": "GQQ",  # Poll Standard Message - Talker ID GQ (QZSS)
    b"\xf0\x06": "GRS",  # GNSS Range Residuals
    b"\xf0\x02": "GSA",  # GNSS DOP and Active Satellites
    b"\xf0\x07": "GST",  # GNSS Pseudo Range Error Statistics
    b"\xf0\x03": "GSV",  # GNSS Satellites in View
    b"\xf0\x0b": "RLM",  # Return Link Message
    b"\xf0\x04": "RMC",  # Recommended Minimum data
    b"\xf0\x0e": "THS",  # TRUE Heading and Status
    b"\xf0\x41": "TXT",  # Text Transmission
    b"\xf0\x0f": "VLW",  # Dual Ground Water Distance
    b"\xf0\x05": "VTG",  # Course over ground and Groundspeed
    b"\xf0\x08": "ZDA",  # Time and Date
}
