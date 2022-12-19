"""
UBX Protocol Input payload definitions
THESE ARE THE PAYLOAD DEFINITIONS FOR _SET_ MESSAGES _TO_ THE RECEIVER
(e.g. configuration and calibration commands; AssistNow payloads)
Created on 27 Sep 2020
Information sourced from u-blox Interface Specifications © 2013-2021, u-blox AG
Created on 4 Sep 2022
:author: vdueck

Based on:
:author: semuadmin
:copyright: SEMU Consulting © 2020
:license: BSD 3-Clause
"""
import gc
gc.collect()
from collections import OrderedDict
gc.collect()
from gnss.msg_dictionaries.ubxtypes_core import (
    U1,
    U2,
    U3,
    U4,
    X1,
)
gc.collect()

from gnss.msg_dictionaries.ubxtypes_get import UBX_PAYLOADS_GET as UBX_GET
gc.collect()

UBX_PAYLOADS_SET = OrderedDict({
    # Configuration Input Messages: i.e. Set Dynamic Model, Set DOP Mask, Set Baud Rate, etc..
    # Messages in the CFG class are used to configure the receiver and read out current configuration values. Any
    # messages in the CFG class sent to the receiver are either acknowledged (with message UBX-ACK-ACK) if
    # processed successfully or rejected (with message UBX-ACK-NAK) if processing unsuccessfully.
    #
    # Most CFG-* GET & SET message payloads are identical, so reference
    # GET definitions here to avoid duplication
    "CFG-CFG": UBX_GET["CFG-CFG"],
    "CFG-MSG": UBX_GET["CFG-MSG"],
    "CFG-NMEA": UBX_GET["CFG-NMEA"],
    "CFG-RATE": UBX_GET["CFG-RATE"],
    "CFG-VALDEL": OrderedDict({
        "version": U1,  # = 0 no transaction, 1 with transaction
        "layers": (
            X1,
            OrderedDict({
                "reserved1": U1,
                "bbr": U1,
                "flash": U1,
            }),
        ),
        "transaction": (  # if version = 1, else reserved
            X1,
            {
                "action": U2,
            },
        ),
        "reserved0": U1,
        "group": ("None", {"keys": U4}),  # repeating group
    }),
    "CFG-VALSET": OrderedDict({
        "version": U1,  # = 0 no transaction, 1 with transaction
        "layers": (
            X1,
            OrderedDict({
                "ram": U1,
                "bbr": U1,
                "flash": U1,
            }),
        ),
        "transaction": (  # if version = 1, else reserved
            X1,
            {
                "action": U2,
            },
        ),
        "reserved0": U1,
        "group": ("None", {"cfgData": U1}),  # repeating group
    }),
    # Firmware Update Messages: i.e. Memory/Flash erase/write, Reboot, Flash identification, etc..
    # Messages in the UPD class are used to update the firmware and identify any attached flash device.
    "UPD-SOS": {
        "cmd": U1,  # 0x00 to create backup in flash, 0x01 to clear backup
        "reserved0": U3,
    },
})
