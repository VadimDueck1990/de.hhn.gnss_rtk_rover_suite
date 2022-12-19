"""
UartReader class.

Connects the ucontroller to the GNSS Receiver
Read messages from the receiver and put it on the corresponding Queue

Created on 4 Sep 2022
:author: vdueck
"""
import gc
import uasyncio

import utils.queue
import gnss.msg_dictionaries.ubxtypes_core as ubt
import gnss.msg_dictionaries.exceptions as ube
from gnss.message_types import PositionData
from gnss.ubx_message import UBXMessage
from gnss.msg_dictionaries.ubxhelpers import calc_checksum, bytes2val

gc.collect()

class UartReader:
    """
    UartReader class.
    """

    _app = None
    _sreader = None
    _gga_q = None
    _cfg_resp_q = None
    _nav_pvt_q = None
    _ack_nack_q = None
    _gga_event = None
    _position_q = None
    _posision: PositionData = None
    _logcount: int

    @classmethod
    def initialize(cls,
                   app: object,
                   sreader: uasyncio.StreamReader,
                   gga_q: utils.queue.Queue,
                   cfg_resp_q: utils.queue.Queue,
                   nav_pvt_q: utils.queue.Queue,
                   ack_nack_q: utils.queue.Queue,
                   ggaevent: uasyncio.Event,
                   position_q: utils.queue.Queue):
        """Initialize class variables.

        :param object app: The calling app
        :param uasyncio.StreamReader sreader: the serial connection to the GNSS Receiver(UART1)
        :param primitives.queue.Queue gga_q: queue for gga messages to ntrip client
        :param primitives.queue.Queue cfg_resp_q: queue for ubx responses to configuration messages
        :param primitives.queue.Queue nav_pvt_q: queue for ubx NAV-PVT get messaged
        :param primitives.queue.Queue ack_nack_q: queue for ubx ACK-NACK messages
        :param primitives.queue.Queue position_q: main queue for position data to web api / client
        :param uasyncio.Event ggaevent: event to synchronize with NTRIP client
        """

        cls._app = app
        cls._sreader = sreader
        cls._gga_q = gga_q
        cls._cfg_resp_q = cfg_resp_q
        cls._nav_pvt_q = nav_pvt_q
        cls._ack_nack_q = ack_nack_q
        cls._gga_event = ggaevent
        cls._position_q = position_q
        cls._posision = PositionData("", 0, "", "", "")
        cls._logcount = 0
    @classmethod
    async def run(cls):
        """
        ASYNC: Read incoming data from UART1 and pass it to the corresponding queue
        """
        gcount = 0
        while True:
            if gcount >= 10:
                gc.collect()
                gcount = 0
            byte1 = await cls._sreader.read(1)
            # if not UBX, NMEA or RTCM3, discard and continue
            if byte1 not in (b"\xb5", b"\x24", b"\xd3"):
                continue
            byte2 = await cls._sreader.read(1)
            bytehdr = byte1 + byte2
            gcount += 1 # count 10 message reads to trigger the garbage collector
            # if it's an NMEA message ('$G' or '$P')
            if bytehdr in ubt.NMEA_HDR:
                # read the rest of the NMEA message from the buffer
                byten = await cls._sreader.readline()  # NMEA protocol is CRLF-terminated
                if "GGA" not in str(byten):
                    continue
                raw_data = bytehdr + byten
                try:
                    checksum_valid = cls._isvalid_cksum(raw_data)
                    if not checksum_valid:
                        print("uart_reader WARN -> NMEA Sentence corrupted, invalid checksum")
                        continue
                except Exception as err:
                    print("Badly formed message {}".format(raw_data))
                    continue
                print("uart_reader -> nmea received: " + str(raw_data))
                cls._logcount = cls._logcount + 1
                cls._get_position_dict(raw_data)
                # if the queue is full then skip. The gga consumer needs to handle messages fast enough otherwise
                # rxBuffer will overflow
                if cls._position_q.empty():
                    await cls._position_q.put(cls._posision)
                if cls._gga_event.is_set():
                    await cls._gga_q.put(raw_data)
                else:
                    continue
            # if it's a UBX message (b'\xb5\x62')
            if bytehdr in ubt.UBX_HDR:
                msg = await cls._parse_ubx(bytehdr)
                if msg.msg_cls == b"\x05":  # ACK-ACK or ACK-NACK message
                    print("uart_reader -> parsed ACK/NACK message: " + str(msg))
                    if cls._ack_nack_q.full():
                        continue
                    await cls._ack_nack_q.put(msg)
                if msg.msg_cls == b"\x06":  # CFG message
                    print("uart_reader -> Parsed CFG Message")
                    if cls._cfg_resp_q.full():
                        continue
                    await cls._cfg_resp_q.put(msg)
                if msg.msg_cls == b"\x01":  # NAV message
                    print("uart_reader -> Parsed NAV Message")
                    if cls._cfg_resp_q.full():
                        continue
                    await cls._nav_pvt_q.put(msg)

    @classmethod
    async def _parse_ubx(cls, hdr: bytes) -> UBXMessage:
        """
        Parse remainder of UBX message.

        :param bytes hdr: UBX header (b'\xb5\x62')
        :return: tuple of (raw_data as bytes, parsed_data as UBXMessage or None)
        :rtype: tuple
        """

        # read the rest of the UBX message from the buffer
        byten = await cls._sreader.read(4)
        clsid = byten[0:1]
        msgid = byten[1:2]
        lenb = byten[2:4]
        leni = int.from_bytes(lenb, "little", False)
        byten = await cls._sreader.read(leni + 2)
        plb = byten[0:leni]
        cksum = byten[leni: leni + 2]
        raw_data = hdr + clsid + msgid + lenb + plb + cksum
        parsed_data = cls.parse(
            raw_data
        )
        return parsed_data

    @staticmethod
    def parse(message: bytes) -> UBXMessage:
        """
        Parse UBX byte stream to UBXMessage object.

        Includes option to validate incoming payload length and checksum
        (the UBXMessage constructor can calculate and assign its own values anyway).

        :param bytes message: binary message to parse
        :return: UBXMessage object
        :rtype: UBXMessage
        :raises: UBXParseError (if data stream contains invalid data or unknown message type)

        """

        msgmode = 0
        validate = ubt.VALCKSUM
        parsebf = True
        scaling = True

        lenm = len(message)
        hdr = message[0:2]
        clsid = message[2:3]
        msgid = message[3:4]
        lenb = message[4:6]
        if lenb == b"\x00\x00":
            payload = None
            leni = 0
        else:
            payload = message[6: lenm - 2]
            leni = len(payload)
        ckm = message[lenm - 2: lenm]
        if payload is not None:
            ckv = calc_checksum(clsid + msgid + lenb + payload)
        else:
            ckv = calc_checksum(clsid + msgid + lenb)
        if validate & ubt.VALCKSUM:
            if hdr != ubt.UBX_HDR:
                raise ube.UBXParseError(
                    ("Invalid message header {} - should be {}".format(hdr, ubt.UBX_HDR))
                )
            if leni != bytes2val(lenb, ubt.U2):
                raise ube.UBXParseError(
                    (
                        "Invalid payload length {}.".format(lenb)
                    )
                )
            if ckm != ckv:
                raise ube.UBXParseError(
                    ("Message checksum {} invalid - should be {}".format(ckm, ckv))
                )
        try:
            if payload is None:
                return UBXMessage(clsid, msgid, msgmode)
            return UBXMessage(
                clsid,
                msgid,
                msgmode,
                payload=payload,
                parsebitfield=parsebf,
                scaling=scaling,
            )
        except KeyError as err:
            modestr = ["GET", "SET", "POLL"][msgmode]
            raise ube.UBXParseError(
                """Unknown message type clsid {}, msgid {}, mode {}.\n
                Check 'msgmode' keyword argument is appropriate for message category""".format(clsid, msgid, modestr)
            ) from err

    @staticmethod
    def _int2hexstr(val: int) -> str:
        """
        Convert integer to hex string representation.

        :param int val: integer < 255 e.g. 31
        :return: hex representation of integer e.g. '1F'
        :rtype: str
        """
        raw_hex = str(hex(val)).upper()
        final_hex = raw_hex[2:]
        if len(final_hex) < 2:
            return "0" + final_hex
        return final_hex

    @staticmethod
    def _get_content(message: object) -> str:
        """
        Get content of raw NMEA message (everything between "$" and "*").

        :param object message: entire message as bytes or string
        :return: content as str
        :rtype: str
        """

        if isinstance(message, bytes):
            message = message.decode("utf-8")
        content, _ = message.strip("$\r\n").split("*", 1)
        return content

    @classmethod
    def _calc_checksum(cls, message: object) -> str:
        """
        Calculate checksum for raw NMEA message.

        :param object message: entire message as bytes or string
        :return: checksum as hex string
        :rtype: str
        """

        content = cls._get_content(message)
        cksum = 0
        for sub in content:
            cksum ^= ord(sub)
        return cls._int2hexstr(cksum)

    @classmethod
    def _isvalid_cksum(cls, message: object) -> bool:
        """
        Validate raw NMEA message checksum.

        :param bytes message: entire message as bytes or string
        :return: checksum valid flag
        :rtype: bool
        """
        _, _, _, cksum = cls._get_parts(message)
        return cksum == cls._calc_checksum(message)

    @staticmethod
    def _get_parts(message: object) -> tuple:
        """
        Get talker, msgid, payload and checksum of raw NMEA message.

        :param object message: entire message as bytes or string
        :return: tuple of (talker as str, msgID as str, payload as list, checksum as str)
        :rtype: tuple
        :raises: NMEAMessageError (if message is badly formed)
        """

        try:
            if isinstance(message, bytes):
                message = message.decode("utf-8")
            content, cksum = message.strip("$\r\n").split("*", 1)

            hdr, payload = content.split(",", 1)
            payload = payload.split(",")
            if hdr[0:1] == "P":  # proprietary
                talker = "P"
                msgid = hdr[1:]
            else:  # standard
                talker = hdr[0:2]
                msgid = hdr[2:]
            return talker, msgid, payload, cksum
        except Exception as err:
            print("Badly formed message {}".format(message))

    @classmethod
    def _get_position_dict(cls, message: object):
        """
        :param object message: entire message as bytes or string
        :return: tuple of (talker as str, msgID as str, payload as list, checksum as str)
        :rtype: tuple
        :raises: NMEAMessageError (if message is badly formed)
        """

        try:
            if isinstance(message, bytes):
                message = message.decode("utf-8")
            content, cksum = message.strip("$\r\n").split("*", 1)
            nmea_fields = content.split(",")
            cls._posision.time = str(nmea_fields[1])
            cls._posision.lat = str(nmea_fields[2])
            cls._posision.lon = str(nmea_fields[4])
            cls._posision.elev = str(nmea_fields[9])
            cls._posision.fixType = int(nmea_fields[6])
        except Exception as err:
            print("Badly formed message {}".format(message))