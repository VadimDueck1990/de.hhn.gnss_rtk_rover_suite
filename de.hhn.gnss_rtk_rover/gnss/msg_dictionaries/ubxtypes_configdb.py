"""
UBX Protocol Configuration Database Keys

Used by CFG_VALGET, CFG_VALSET and CFG_VALDEL message types

Format:
"keyname": (keyID, "type")

Created on 4 Sep 2022
:author: vdueck

Based on:
:author: semuadmin
:copyright: SEMU Consulting © 2020
:license: BSD 3-Clause
"""
# pylint: disable=too-many-lines

from gnss.msg_dictionaries.ubxtypes_core import (
    L,
    U4,
)

# memory layer designators for CFG_VALSET & CFG_VALDEL
SET_LAYER_RAM = 1
SET_LAYER_BBR = 2
SET_LAYER_FLASH = 4

# memory layer designators for CFG_VALGET
POLL_LAYER_RAM = 0
POLL_LAYER_BBR = 1
POLL_LAYER_FLASH = 2
POLL_LAYER_DEFAULT = 7

# transaction state designators for CFG_VALSET & CFG_VALDEL
TXN_NONE = 0
TXN_START = 1
TXN_ONGOING = 2
TXN_COMMIT = 3

# bits 28..30 of Configuration KeyID represent
# storage length of Configuration Value in bytes
# KeyID >> 28 & 0b111
UBX_CONFIG_STORSIZE = {
    0x01: 1,
    0x02: 1,
    0x03: 2,
    0x04: 4,
    0x05: 8,
}

# NB: hyphens have been substituted for underscores in
# key names to make them valid attribute names
#
# PLEASE KEEP DICT SORTED BY KEY NAME
#
UBX_CONFIG_DATABASE = {
    "CFG_SIGNAL_BDS_ENA": (0x10310022, L),
    "CFG_SIGNAL_GAL_ENA": (0x10310021, L),
    "CFG_SIGNAL_GLO_ENA": (0x10310025, L),
    "CFG_SIGNAL_GPS_ENA": (0x1031001F, L),
    "CFG_SIGNAL_IMES_ENA": (0x10310023, L),
    "CFG_SIGNAL_QZSS_ENA": (0x10310024, L),
    "CFG_SIGNAL_SBAS_ENA": (0x10310020, L),
    "CFG-NMEA-HIGHPREC": (0x10930006, L),
    "CFG_UART2_BAUDRATE": (0x40530001, U4),
}
