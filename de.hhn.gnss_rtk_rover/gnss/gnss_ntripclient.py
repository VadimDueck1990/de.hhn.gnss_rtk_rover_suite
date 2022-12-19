"""
NTRIP Client class

Transmits client position from ZED-F9P to NTRIP caster
at specified interval
correction data from NTRIP caster and sending the
correction data to the ZED-F9P over UART

Created on 10 Oct 2022
:author: vdueck
"""
from utils.mem_debug import debug_gc
debug_gc()
import utils.queue
from gnss.gnss_handler import GnssHandler
from gnss.rtcm_reader import RTCMReader
import binascii
import uasyncio
from uasyncio import Event
from machine import UART
import time
from utils.queue import Queue
import usocket
from gnss.msg_dictionaries.ubxtypes_core import RTCM3_PROTOCOL, ERR_IGNORE
from gnss.msg_dictionaries.exceptions import (
    RTCMParseError,
    RTCMMessageError,
    RTCMTypeError,
)
from utils.globals import (
    DEFAULT_BUFSIZE,
    OUTPORT_NTRIP,
    NTRIP_USER,
    NTRIP_PW,
    NTRIP_SERVER,
    MOUNTPOINT,
    GGA_INTERVAL,
)

TIMEOUT = 10
VERSION = "0.1.0"
USERAGENT = f"HHN BW NTRIP Client/{VERSION}"
NTRIP_HEADERS = {
    "Ntrip-Version": "Ntrip/2.0",
    "User-Agent": USERAGENT,
}
GGALIVE = 0
GGAFIXED = 1


class GNSSNTRIPClient:
    """
    NTRIP client class.
    """

    def __init__(self,
                 rtcmoutput: UART,
                 app: object,
                 gga_q: utils.queue.Queue,
                 ggaevent: uasyncio.Event):
        """
        Constructor.

        :param object app: application from which this class is invoked (None)
        :param object rtcmoutput: UART connection for rtcm data to ZED-F9P
        :param object gga_q: The Queue with GGA data from the receiver
        :param Event ggaevent: event to tell the UartReader to put a GGA sentence on the gga_q
        """
        self.__app = app  # Reference to calling application class (if applicable)
        self._ntripqueue = Queue()
        self._socket = None
        self._swriter = None
        self._sreader = None
        self._task = None
        self._read_gga_event = ggaevent
        self._output = uasyncio.StreamWriter(rtcmoutput)
        self._last_gga = time.ticks_ms()
        self._gga_queue = gga_q
        self._first_start = True

        # persist settings to allow any calling app to retrieve them
        self._settings = {
            "server": "",
            "port": "2101",
            "mountpoint": "",
            "distance": "",
            "version": "2.0",
            "user": "anon",
            "password": "password",
            "ggainterval": "None",
            "sourcetable": [],
            "reflat": "",
            "reflon": "",
            "refalt": "",
            "refsep": "",
        }

    @property
    def settings(self):
        """
        Getter for NTRIP settings.
        """
        return self._settings


    async def run(self, ntrip_lock: uasyncio.Lock, stopevent: uasyncio.Event):
        """
        Open NTRIP server connection.
        Opens socket to NTRIP server and reads incoming data.
        :param Lock ntrip_lock: used to synchronise the RTCMEnabled Flag
        :param Event stopevent: used to start and stop the ntrip-client / is set by GnssHandler and RequestHandler
        """
        self._task = uasyncio.current_task()
        self._settings["server"] = NTRIP_SERVER
        self._settings["port"] = int(OUTPORT_NTRIP)
        self._settings["mountpoint"] = mountpoint = MOUNTPOINT
        self._settings["version"] = "2.0"
        self._settings["user"] = NTRIP_USER
        self._settings["password"] = NTRIP_PW
        self._settings["ggainterval"] = int(GGA_INTERVAL * 1000)
        print("gnssntripclient -> starting ntrip reading task")

        stopevent.set()
        server = self._settings["server"]
        port = int(self._settings["port"])
        mountpoint = self._settings["mountpoint"]
        ggainterval = int(self._settings["ggainterval"])

        while True:
            if not stopevent.is_set():
                try:
                    self._socket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
                    self._socket.settimeout(TIMEOUT)
                    addr = usocket.getaddrinfo(server, port)[0][-1]
                    self._socket.connect(addr)
                    msg = self._formatGET(self._settings)
                    print(str(msg))
                    self._swriter = uasyncio.StreamWriter(self._socket)
                    self._sreader = uasyncio.StreamReader(self._socket)
                    self._swriter.write(msg)
                    await self._swriter.drain()
                    async with ntrip_lock:
                        GnssHandler.rtcm_enabled = True
                    if mountpoint != "":
                        await self._send_GGA(ggainterval)

                        try:
                            await self._do_data(self._sreader, stopevent, ggainterval, self._output, ntrip_lock)
                        except Exception as ex:
                            print(Exception)
                            stopevent.set()
                            await self._swriter.wait_closed()
                            await self._sreader.wait_closed()
                            async with ntrip_lock:
                                GnssHandler.rtcm_enabled = False
                        else:
                            await uasyncio.sleep(1)
                            async with ntrip_lock:
                                GnssHandler.rtcm_enabled = False
                except Exception as ex:
                    print(Exception)
                    stopevent.set()
                    await self._swriter.wait_closed()
                    await self._sreader.wait_closed()
                    async with ntrip_lock:
                        GnssHandler.rtcm_enabled = False
            else:
                await uasyncio.sleep(1)
                async with ntrip_lock:
                    GnssHandler.rtcm_enabled = False





    @staticmethod
    def _formatGET(settings: dict) -> bytes:
        """
        THREADED
        Format HTTP GET Request.

        :param dict settings: settings dictionary
        :return: formatted HTTP GET request
        :rtype: bytes
        """

        host = f"{settings['server']}:{settings['port']}"
        mountpoint = settings["mountpoint"]
        version = settings["version"]
        user = settings["user"]
        password = settings["password"]

        mountpoint = "/" + mountpoint  # sourcetable request
        user = user + ":" + password
        user = bytes(user, 'utf-8')
        user = binascii.b2a_base64(user)

        reqline1 = f"GET {mountpoint} HTTP/1.1\r\n"
        reqline2 = f"User-Agent: {USERAGENT}\r\n"
        reqline3 = f"Host: {host}\r\n"
        reqline4 = f"Authorization: Basic {user.decode('utf-8')}\r\n"
        reqline5 = f"Ntrip-Version: Ntrip/{version}\r\n"
        req = reqline1 + reqline2 + reqline3 + reqline4 + reqline5 + "\r\n"  # NECESSARY!!!
        return bytes(req, 'utf-8')

    async def _send_GGA(self, ggainterval: int):
        """
        THREADED
        Send NMEA GGA sentence to NTRIP server at prescribed interval.

        :param int ggainterval: tells how often the gga should be send to the ntrip-caster
        """
        if time.ticks_diff(time.ticks_ms(), self._last_gga) > ggainterval or self._first_start:
            self._read_gga_event.set()
            raw_data = await self._gga_queue.get()
            self._read_gga_event.clear()
            if raw_data is not None:
                self._swriter.write(raw_data)
                await self._swriter.drain()
                print("Sending gga to caster: " + str(raw_data))
            self._last_gga = time.ticks_ms()
            self._first_start = False

    async def _do_data(self,
                       sock: uasyncio.StreamReader,
                       stopevent: Event,
                       ggainterval: int,
                       output: uasyncio.StreamWriter,
                       ntrip_lock: uasyncio.Lock):
        """
        ASYNC
        Read and parse incoming NTRIP RTCM3 data stream.

        :param StreamReader sock: socket
        :param Event stopevent: stop event
        :param int ggainterval: GGA transmission interval seconds
        :param uasyncio.StreamWriter output: output stream for RTCM3 messages
        """
        print("ntrip begin do_data " + str(time.ticks_ms()))
        # RTCMReader will wrap socket as SocketStream
        ubr = RTCMReader(
            sock,
            protfilter=RTCM3_PROTOCOL,
            quitonerror=ERR_IGNORE,
            bufsize=DEFAULT_BUFSIZE,
            labelmsm=True,
        )
        raw_data = None
        async with ntrip_lock:
            GnssHandler.rtcm_enabled = True
        while not stopevent.is_set():
            try:
                raw_data = await ubr.read()
                if raw_data is not None:
                    await self._do_write(output, raw_data)
                await self._send_GGA(ggainterval)
            except (
                RTCMMessageError,
                RTCMParseError,
                RTCMTypeError,
            ) as err:
                print("gnssntripclient -> Error parsing rtcm stream")
                continue

    async def _do_write(self, output: uasyncio.StreamWriter, raw: bytes):
        """
        ASYNC
        Send RTCM3 data to designated output medium.


        :param uasyncio.Streamwriter output: writeable output medium for RTCM3 data
        :param bytes raw: raw data
        """
        output.write(raw)
        await output.drain()
