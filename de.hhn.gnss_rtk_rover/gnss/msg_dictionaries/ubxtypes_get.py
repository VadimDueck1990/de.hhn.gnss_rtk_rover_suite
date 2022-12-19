"""
UBX Protocol Output payload definitions

THESE ARE THE PAYLOAD DEFINITIONS FOR _GET_ MESSAGES _FROM_ THE RECEIVER
(e.g. Periodic Navigation Data; Poll Responses; Info messages)
Created on 27 Sep 2020
Information sourced from u-blox Interface Specifications © 2013-2021, u-blox AG
Created on 4 Sep 2022
:author: vdueck

Based on:
:author: semuadmin
:copyright: SEMU Consulting © 2020
:license: BSD 3-Clause
"""
from collections import OrderedDict

from gnss.msg_dictionaries.ubxtypes_core import (
    C2,
    I1,
    I2,
    I4,
    U1,
    U2,
    U3,
    U4,
    U5,
    U6,
    U9,
    X1,
    X2,
    X4,
    SCAL7,
    SCAL5,
    SCAL2,
    SCAL1,
)


UBX_PAYLOADS_GET = OrderedDict({
    "ACK-ACK": OrderedDict({"clsID": U1, "msgID": U1}),
    "ACK-NAK": OrderedDict({"clsID": U1, "msgID": U1}),
    # Configuration Input Messages: i.e. Set Dynamic Model, Set DOP Mask, Set Baud Rate, etc..
    # Messages in the CFG class are used to configure the receiver and read out current configuration values. Any
    # messages in the CFG class sent to the receiver are either acknowledged (with message UBX-ACK-ACK) if
    # processed successfully or rejected (with message UBX-ACK-NAK) if processing unsuccessfully.
    "CFG-CFG": OrderedDict({
        "clearMask": X4,
        "saveMask": X4,
        "loadMask": X4,
        "deviceMask": (
            X1,
            OrderedDict({
                "devBBR": U1,
                "devFlash": U1,
                "devEEPROM": U1,
                "reserved1": U1,
                "devSpiFlash": U1,
            }),
        ),
    }),
    "CFG-MSG": OrderedDict({
        "msgClass": U1,
        "msgID": U1,
        "rateDDC": U1,
        "rateUART1": U1,
        "rateUART2": U1,
        "rateUSB": U1,
        "rateSPI": U1,
        "reserved": U1,
    }),
    "CFG-NMEA": OrderedDict({  # preferred version length 20
        "filter": (
            X1,
            OrderedDict({
                "posFilt": U1,
                "mskPosFilt": U1,
                "timeFilt": U1,
                "dateFilt": U1,
                "gpsOnlyFilter": U1,
                "trackFilt": U1,
            }),
        ),
        "nmeaVersion": U1,
        "numSV": U1,
        "flags": (
            X1,
            OrderedDict({
                "compat": U1,
                "consider": U1,
                "limit82": U1,
                "highPrec": U1,
            }),
        ),
        "gnssToFilter": (
            X4,
            OrderedDict({
                "gps": U1,
                "sbas": U1,
                "galileo": U1,
                "reserved2": U1,
                "qzss": U1,
                "glonass": U1,
                "beidou": U1,
            }),
        ),
        "svNumbering": U1,
        "mainTalkerId": U1,
        "gsvTalkerId": U1,
        "version": U1,
        "bdsTalkerId": C2,
        "reserved1": U6,
    }),
    "CFG-PRT": OrderedDict({
        "portID": U1,
        "reserved0": U1,
        "txReady": (
            X2,
            OrderedDict({
                "enable": U1,
                "pol": U1,
                "pin": U5,
                "thres": U9,
            }),
        ),
        "UARTmode": (
            X4,
            OrderedDict({
                "reserved2": U6,
                "charLen": U2,
                "reserved3": U1,
                "parity": U3,
                "nStopBits": U2,
            }),
        ),
        "baudRate": U4,
        "inProtoMask": (
            X2,
            OrderedDict({
                "inUBX": U1,
                "inNMEA": U1,
                "inRTCM": U1,
                "reserved4": U2,
                "inRTCM3": U1,
            }),
        ),
        "outProtoMask": (
            X2,
            OrderedDict({
                "outUBX": U1,
                "outNMEA": U1,
                "reserved5": U3,
                "outRTCM3": U1,
            }),
        ),
        "flags": (
            X2,
            OrderedDict({
                "reserved6": U1,
                "extendedTxTimeout": U1,
            }),
        ),
        "reserved1": U2,
    }),
    "CFG-RATE": OrderedDict({"measRate": U2, "navRate": U2, "timeRef": U2}),
    "CFG-VALGET": OrderedDict({
        "version": U1,
        "layer": U1,
        "position": U2,
        "group": ("None", OrderedDict({"cfgData": U1})),  # repeating group
    }),
    # NB: special handling for NAV-HPPOS* message types;
    # private standard and high precision attributes are
    # combined into a single public attribute in
    # accordance with interface specification
    "NAV-PVT": OrderedDict({
        "iTOW": U4,
        "year": U2,
        "month": U1,
        "day": U1,
        "hour": U1,
        "min": U1,
        "second": U1,
        "valid": (
            X1,
            OrderedDict({
                "validDate": U1,
                "validTime": U1,
                "fullyResolved": U1,
                "validMag": U1,
            }),
        ),
        "tAcc": U4,
        "nano": I4,
        "fixType": U1,
        "flags": (
            X1,
            OrderedDict({
                "gnssFixOk": U1,
                "difSoln": U1,
                "psmState": U3,
                "headVehValid": U1,
                "carrSoln": U2,
            }),
        ),
        "flags2": (
            X1,
            OrderedDict({
                "reserved": U5,
                "confirmedAvai": U1,
                "confirmedDate": U1,
                "confirmedTime": U1,
            }),
        ),
        "numSV": U1,
        "lon": [I4, SCAL7],
        "lat": [I4, SCAL7],
        "height": I4,
        "hMSL": I4,
        "hAcc": U4,
        "vAcc": U4,
        "velN": I4,
        "velE": I4,
        "velD": I4,
        "gSpeed": I4,
        "headMot": [I4, SCAL5],
        "sAcc": U4,
        "headAcc": [U4, SCAL5],
        "pDOP": [U2, SCAL2],
        "flags3": (
            X2,
            OrderedDict({
                "invalidLlh": U1,
                "lastCorrectionAge": U4,
            }),
        ),
        "reserved0": U4,  # NB this is incorrectly stated as U5 in older documentation
        "headVeh": [I4, SCAL5],
        "magDec": [I2, SCAL2],
        "magAcc": [U2, SCAL2],
    }),
    "NAV-SAT": OrderedDict({
        "iTOW": U4,
        "version": U1,
        "numSvs": U1,
        "reserved0": U2,
        "group": (  # repeating group * numSvs
            "numSvs",
            OrderedDict({
                "gnssId": U1,
                "svId": U1,
                "cno": U1,
                "elev": I1,
                "azim": I2,
                "prRes": [I2, SCAL1],
                "flags": (
                    X4,
                    OrderedDict({
                        "qualityInd": U3,
                        "svUsed": U1,
                        "health": U2,
                        "diffCorr": U1,
                        "smoothed": U1,
                        "orbitSource": U3,
                        "ephAvail": U1,
                        "almAvail": U1,
                        "anoAvail": U1,
                        "aopAvail": U1,
                        "reserved13": U1,
                        "sbasCorrUsed": U1,
                        "rtcmCorrUsed": U1,
                        "slasCorrUsed": U1,
                        "spartnCorrUsed": U1,
                        "prCorrUsed": U1,
                        "crCorrUsed": U1,
                        "doCorrUsed": U1,
                    }),
                ),
            }),
        ),
    }),
    "NAV-STATUS": OrderedDict({
        "iTOW": U4,
        "gpsFix": U1,
        "flags": (
            X1,
            OrderedDict({
                "gpsFixOk": U1,
                "diffSoln": U1,
                "wknSet": U1,
                "towSet": U1,
            }),
        ),
        "fixStat": (
            X1,
            OrderedDict({
                "diffCorr": U1,
                "carrSolnValid": U1,
                "reserved0": U4,
                "mapMatching": U2,
            }),
        ),
        "flags2": (
            X1,
            OrderedDict({
                "psmState": U2,
                "reserved1": U1,
                "spoofDetState": U2,
                "reserved2": U1,
                "carrSoln": U2,
            }),
        ),
        "ttff": U4,
        "msss": U4,
    }),
    # Firmware Update Messages: i.e. Memory/Flash erase/write, Reboot, Flash identification, etc..
    # Messages in the UPD class are used to update the firmware and identify any attached flash device.
    "UPD-SOS": OrderedDict({  # System restored from backup
        "cmd": U1,
        "reserved0": U3,
        "response": U1,
        "reserved1": U3,
    }),
    # UBX nominal payload definition, used as fallback where no documented
    # payload definition is available.
    "UBX-NOMINAL": OrderedDict({
        "group": (
            "None",
            {
                "data": X1,
            },
        )
    }),
})
