"""
GnssHandler class.

Connects the ucontroller to the GNSS receiver and handles the connection.
Queries different ublox messages from the GNSSreceiver and handles incoming data


Created on 4 Sep 2022
:author: vdueck
"""
import gc

import uasyncio
from gnss.message_types import PositionData, Accuracy
from utils.mem_debug import debug_gc
import utime
from utils.queue import Queue
from gnss.ubx_message import UBXMessage
from gnss.msg_dictionaries.ubxtypes_configdb import SET_LAYER_RAM, POLL_LAYER_RAM
from gnss.msg_dictionaries.ubxtypes_core import SET, GET, UBX_MSGIDS
gc.collect()


class GnssHandler:
    """
    GnssHandler class.
    """
    _app = None
    _gga_q = None
    _cfg_response_q = None
    _nav_msg_q = None
    _ack_nack_q = None
    _msg_q = None
    _pos_q = None

    rtcm_enabled = None
    ntrip_lock = None
    ntrip_stop_event = None

    _update_interval = None
    _last_pos_time = None
    _last_acc_time = None
    _last_ntrip_time = None

    # cache variables to save uart requests
    _position: PositionData
    _accuracy: Accuracy

    # predefined strings
    _config_key_gps = "CFG_SIGNAL_GPS_ENA"
    _config_key_gal = "CFG_SIGNAL_GAL_ENA"
    _config_key_glo = "CFG_SIGNAL_GLO_ENA"
    _config_key_bds = "CFG_SIGNAL_BDS_ENA"
    _config_key_hpm = "CFG-NMEA-HIGHPREC"
    _config_key_uart2_baud = "CFG_UART2_BAUDRATE"

    _nav_cls = "NAV"
    _cfg_cls = "CFG"
    _cfg_rate = "CFG-RATE"
    _cfg_msg = "CFG-MSG"
    _nav_pvt = "NAV-PVT"
    _nav_sat = "NAV-SAT"

    @classmethod
    def initialize(cls,
                   app: object,
                   gga_q: Queue,
                   cfg_resp_q: Queue,
                   nav_pvt_q: Queue,
                   ack_nack_q: Queue,
                   msg_q: Queue,
                   pos_q: Queue,
                   ntrip_lock: uasyncio.Lock,
                   stop_event: uasyncio.Event):
        """Initialization method.
        :param object app: The calling app
        :param primitives.queue.Queue gga_q: queue for incoming gga messages
        :param primitives.queue.Queue cfg_resp_q: queue for ubx responses to configuration messages
        :param primitives.queue.Queue nav_pvt_q: queue for incoming ubx NAV-PVT get messaged
        :param primitives.queue.Queue ack_nack_q: queue for incoming ubx ACK-NACK messages
        :param primitives.queue.Queue msg_q: queue for outgoing ubx messages
        :param primitives.queue.Queue pos_q: queue for the main position data
        :param uasyncio.Lock ntrip_lock: lock for reading the rtcm_enabled flag
        :param uasyncio.Event stop_event: handling the ntrip client (stop/resume)
        """
        cls._app = app
        cls._gga_q = gga_q
        cls._cfg_response_q = cfg_resp_q
        cls._nav_msg_q = nav_pvt_q
        cls._ack_nack_q = ack_nack_q
        cls._msg_q = msg_q
        cls._pos_q = pos_q
        cls.rtcm_enabled = False
        cls.ntrip_lock = ntrip_lock
        cls.ntrip_stop_event = stop_event

        cls._update_interval = 5000
        cls._last_pos_time = utime.ticks_ms()
        cls._last_acc_time = utime.ticks_ms()
        cls._last_ntrip_time = utime.ticks_ms()

        cls._accuracy = Accuracy(0, 0)

        gc.collect()

    @classmethod
    async def set_update_rate(cls, update_rate: int) -> bool:
        """
        ASYNC: Sets the update rate of the GNSS receiver(how often a GGA sentence is sent over UART1)

        :param int update_rate: the update rate in ms. min=50 max=5000
        :return: True if successful, False if failed
        :rtype: bool
        """

        await cls._flush_receive_qs()
        if update_rate < 50:
            update_rate = 50
        if update_rate > 5000:
            update_rate = 5000

        msg = UBXMessage(
            cls._cfg_cls,
            cls._cfg_rate,
            SET,
            measRate=update_rate,
            navRate=1,
            timeRef=1
        )
        await cls._msg_q.put(msg.serialize())
        ack = await cls._ack_nack_q.get()
        if ack.msg_id == b'\x01':  # ACK-ACK
            gc.collect()
            return True
        else:
            gc.collect()
            return False  # ACK-NACK

    @classmethod
    async def get_update_rate(cls) -> int:
        """
        ASYNC: Gets the update rate of the GNSS receiver(how often a GGA sentence is sent over UART1)

        :return: number representing ms between updates
        :rtype: int
        """
        await cls._flush_receive_qs()
        msg = UBXMessage(
            cls._cfg_cls,
            cls._cfg_rate,
            GET,
        )
        await cls._msg_q.put(msg.serialize())
        cfg = await cls._cfg_response_q.get()
        result = cfg.__dict__["measRate"]
        gc.collect()
        return int(result)

    @classmethod
    async def set_satellite_systems(cls,
                                    gps: int,
                                    gal: int,
                                    glo: int,
                                    bds: int) -> bool:
        """
        ASYNC: Configure the satellite systems the GNSS receiver should use in his navigation computing

        :param int gps: GPS On=1 / Off=0
        :param int glo: GLONASS On=1 / Off=0
        :param int gal: Galileo On=1 / Off=0
        :param int bds: BeiDou On=1 / Off=0
        :return: True if successful, False if failed
        :rtype: bool
        """
        await cls._flush_receive_qs()
        layer = SET_LAYER_RAM  # volatile memory
        transaction = 0
        cfg_data = [(cls._config_key_gps, gps),
                    (cls._config_key_gal, gal),
                    (cls._config_key_glo, glo),
                    (cls._config_key_bds, bds)]
        msg = UBXMessage.config_set(layer, transaction, cfg_data)
        await cls._msg_q.put(msg.serialize())
        ack = await cls._ack_nack_q.get()
        if ack.msg_id == b'\x01':  # ACK-ACK
            gc.collect()
            return True
        else:
            gc.collect()
            return False  # ACK-NACK

    @classmethod
    async def get_satellite_systems(cls) -> dict:
        """
        ASYNC: Get the satellite systems the GNSS receiver uses in his navigation computing
        e.g.:
        {
            "gps": 1,
            "glo": 0,
            "gal": 1,
            "bds": 0
        }
        :return: Dictionary with satellite systems and values
        :rtype: dict if successful, None if failed
        """

        await cls._flush_receive_qs()
        layer = POLL_LAYER_RAM  # volatile memory
        position = 0
        keys = [cls._config_key_gps, cls._config_key_gal, cls._config_key_glo, cls._config_key_bds]
        msg = UBXMessage.config_poll(layer, position, keys)
        await cls._msg_q.put(msg.serialize())
        cfg = await cls._cfg_response_q.get()
        val_gps = cfg.__dict__[cls._config_key_gps]
        val_glo = cfg.__dict__[cls._config_key_glo]
        val_gal = cfg.__dict__[cls._config_key_gal]
        val_bds = cfg.__dict__[cls._config_key_bds]
        result = {
            "gps": int(val_gps),
            "glo": int(val_glo),
            "gal": int(val_gal),
            "bds": int(val_bds),
        }
        gc.collect()
        return result

    @classmethod
    async def get_precision(cls, realtime: bool) -> Accuracy:
        """
        ASYNC: Gets precision of measurement

        :return: hAcc, Vacc
        :rtype: int, int
        """
        if utime.ticks_diff(utime.ticks_ms(), cls._last_acc_time) < cls._update_interval:
            if not realtime:
                return cls._accuracy

        await cls._flush_receive_qs()
        msg = UBXMessage(
            cls._nav_cls,
            cls._nav_pvt,
            GET
        )
        await cls._msg_q.put(msg.serialize())
        nav = await cls._nav_msg_q.get()
        # if ack.msg_id == b'\x01':  # ACK-ACK
        h_acc = nav.__dict__["hAcc"]
        v_acc = nav.__dict__["vAcc"]
        cls._accuracy = Accuracy(h_acc, v_acc)
        cls._last_acc_time = utime.ticks_ms()
        gc.collect()
        return cls._accuracy

    @classmethod
    async def get_satellites_in_use(cls) -> dict:
        """
        TODO: funktioniert nicht als ubx-Abfrage, frisst den gesamten heap!!!
        ASYNC: Get the satellites used in navigation
        ATTENTION: Method does not work yet. Uses to much heap to create NAV-SAT Message!!!!!!!!
        :return: UBXMessage NAV-SAT containing satellites with details
        :rtype: UBXMessage
        """
        gc.collect()
        await cls._flush_receive_qs()
        msg = UBXMessage(
            cls._nav_cls,
            cls._nav_sat,
            GET
        )
        debug_gc()
        await cls._msg_q.put(msg.serialize())
        nav = await cls._nav_msg_q.get()
        gc.collect()
        return nav

    @classmethod
    async def set_high_precision_mode(cls, enable: int) -> bool:
        """
        ASYNC: Enable/Disable High Precision mode

        :param int enable: 0 = enable / 1 = disable
        :return: True if successful, False if failed
        :rtype: bool
        """
        await cls._flush_receive_qs()
        layer = SET_LAYER_RAM  # volatile memory
        transaction = 0
        cfg_data = [(cls._config_key_hpm, enable)]
        msg = UBXMessage.config_set(layer, transaction, cfg_data)
        await cls._msg_q.put(msg.serialize())
        ack = await cls._ack_nack_q.get()
        if ack.msg_id == b'\x01':  # ACK-ACK
            gc.collect()
            return True
        else:
            gc.collect()
            return False  # ACK-NACK

    @classmethod
    def enableNTRIP(cls, enable: int):
        """
        Enable/Disable NTRIP client
        sets/clears the stopevent for the GNSSNtripClient.run() task

        :param int enable: 0 = enable / 1 = disable
        :return: True if successful, False if failed
        :rtype: bool
        """
        if enable == 1:
            cls.ntrip_stop_event.clear()
        else:
            cls.ntrip_stop_event.set()

    @classmethod
    async def get_ntrip_status(cls) -> bool:
        """
        Enable/Disable NTRIP client
        sets/clears the stopevent for the GNSSNtripClient.run() task

        :return: True if successful, False if failed
        :rtype: bool
        """
        async with cls.ntrip_lock:
            if GnssHandler.rtcm_enabled:
                return True
            else:
                return False

    @classmethod
    async def get_position(cls) -> PositionData:
        """
        ASYNC: Gets the position dictionary with: time, latitude, longitude, elevation and fixtype

        :return: Position Data
        :rtype: PositionData
        """
        await cls._flush_receive_qs()
        position = await cls._pos_q.get()
        return position

    @classmethod
    async def set_minimum_nmea_msgs(cls):
        """
        ASYNC: Deactivate all NMEA messages on UART1, except NMEA-GGA
        """
        await cls._flush_receive_qs()
        count = 0
        for (msgid, msgname) in UBX_MSGIDS.items():
            if msgid[0] == 0xf0:  # NMEA
                if msgid[1] == 0x00:  # NMEA-GGA
                    rate = 1
                else:
                    rate = 0
                msgnmea = UBXMessage(
                    cls._cfg_cls,
                    cls._cfg_msg,
                    SET,
                    msgClass=msgid[0],
                    msgID=msgid[1],
                    rateUART1=rate,
                    rateUSB=0,
                )
                await cls._msg_q.put(msgnmea.serialize())
                count = count + 1
                gc.collect()
        while not cls._ack_nack_q.empty:
            await cls._ack_nack_q.get()
        gc.collect()

    @classmethod
    async def _flush_receive_qs(cls):
        """
        ASYNC: Empty all receiving queues
        """
        while not cls._ack_nack_q.empty:
            await cls._ack_nack_q.get()
        while not cls._nav_msg_q.empty:
            await cls._nav_msg_q.get()
        while not cls._cfg_response_q.empty:
            await cls._cfg_response_q.get()


