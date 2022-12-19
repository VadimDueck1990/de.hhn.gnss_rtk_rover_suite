"""
UBX Custom Exception Types

Created on 4 Sep 2022
:author: vdueck

Based on:
:author: semuadmin
:copyright: SEMU Consulting © 2020
:license: BSD 3-Clause
"""

class UBXParseError(Exception):
    """UBX Parsing error"""

class UBXStreamError(Exception):
    """UBX Streaming error."""

class UBXMessageError(Exception):
    """UBX Undefined message class/id."""

class UBXTypeError(Exception):
    """UBX Undefined payload attribute type."""

class NMEAMessageError(Exception):
    """NMEA Undefined message class/id."""

class RTCMParseError(Exception):
    """RTCM Parsing error."""

class RTCMStreamError(Exception):
    """RTCM Streaming error."""

class RTCMMessageError(Exception):
    """RTCM Undefined message class/id."""

class RTCMTypeError(Exception):
    """RTCM Undefined payload attribute type."""