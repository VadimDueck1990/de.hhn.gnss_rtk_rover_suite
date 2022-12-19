"""
RequestHandler class.
Handles the web requests and manages the websocket connection
Created on 4 Sep 2022
:author: vdueck
"""
import gc
import ujson
import uasyncio
import utime

from gnss.message_types import PositionData, Accuracy, RealTimeMessage
from gnss.gnss_handler import GnssHandler
from web_api.microWebSrv import MicroWebSrv
from utils.queue import Queue


class RequestHandler:
    """
    RequestHandler class.
    """

    _app = None
    _position_q = None
    _route_handlers = None
    _srv = None
    _ntrip_stop_event = None
    _rtcm_lock = None
    _last_pos = None
    _acc_interval = None
    _send_position_task = None

    # data cache to save on UART reads/writes
    _position_data = None

    @classmethod
    async def initialize(cls,
                         app: object,
                         queue: Queue,
                         ntrip_stop_event: uasyncio.Event,
                         rtcm_lock: uasyncio.Lock):
        """Initializes the RequestHandler
        Sets the necessary queues and starts the webserver

        :param object app: The calling app
        :param Queue queue: the queue with the incoming postion messages
        :param ntrip_stop_event: used to control the start/stop of ntrip-client
        :param Lock rtcm_lock: used to get/set the rtcm flag
        """

        cls._app = app
        cls._position_q = queue
        cls._ntrip_stop_event = ntrip_stop_event
        cls._rtcm_lock = rtcm_lock

        cls._position_data = GnssHandler.get_position()
        cls._last_pos = utime.ticks_ms()

        _route_handlers = [("/rate", "GET", cls._getUpdateRate),
                           ("/rate", "POST", cls._setUpdateRate),
                           ("/precision", "GET", cls._getPrecision),
                           ("/satellites", "GET", cls._getSatellites),
                           ("/position", "GET", cls._getPosition),
                           ("/ntrip", "POST", cls._enableNTRIP),
                           ("/ntrip", "GET", cls._getNtripStatus),
                           ("/satsystems", "GET", cls._getSatSystems),
                           ("/satsystems", "POST", cls._setSatSystems)]

        srv = MicroWebSrv(routeHandlers=_route_handlers, webPath='/web_api/www/')
        srv.MaxWebSocketRecvLen = 256
        srv.AcceptWebSocketCallback = cls.cb_accept_ws
        await srv.Start()

    @classmethod
    async def _getUpdateRate(cls, http_client, http_response):
        """
        ASYNC: Handles get update rate requests from the web

        :param MicroWebSrv._client http client: holds the client_connection
        :param MicroWebSrv._response http_response: holds the answer to the client
        """
        try:
            rate = await GnssHandler.get_update_rate()
            response = {"updateRate": rate}
            await http_response.WriteResponseJSONOk(response)
        except Exception as ex:
            await http_response.WriteResponseJSONError(400)

    @classmethod
    async def _setUpdateRate(cls, http_client, http_response):
        """
        ASYNC: Handles set update rate requests from the web
        Gets the rate from request body and forwards it to the GnssHandler

        :param MicroWebSrv._client http client: holds the client_connection
        :param MicroWebSrv._response http_response: holds the answer to the client
        """
        payload = await http_client.ReadRequestContentAsJSON()
        try:
            rate = payload["updateRate"]
            print("set update rate triggered, rate: " + str(rate))
            result = await GnssHandler.set_update_rate(rate)
            await http_response.WriteResponseOk()
        except Exception as ex:
            await http_response.WriteResponseJSONError(400)

    @classmethod
    async def _getSatellites(cls, http_client, http_response):
        """
        ASYNC: Handles requests for satellite data
        TODO: Not functioning!

        :param MicroWebSrv._client http client: holds the client_connection
        :param MicroWebSrv._response http_response: holds the answer to the client
        """
        try:
            navsat = await GnssHandler.get_satellites_in_use()
            response = ujson.dumps(navsat)
            await http_response.WriteResponseJSONOk(response)
        except Exception as ex:
            await http_response.WriteResponseJSONError(400)

    @classmethod
    async def _getPrecision(cls, http_client, http_response):
        """
        ASYNC: Handles requests for accuracy from the web
        Gets the accuracy from GnssHandler and sends it to client

        :param MicroWebSrv._client http client: holds the client_connection
        :param MicroWebSrv._response http_response: holds the answer to the client
        """
        try:
            precision = await GnssHandler.get_precision(False)
            data = ujson.dumps(precision.__dict__)
            await http_response.WriteResponseJSONOk(data)
        except Exception as ex:
            await http_response.WriteResponseJSONError(400)


    @classmethod
    async def _enableNTRIP(cls, http_client, http_response):
        """
        ASYNC: Handles requests for setting the rtcm correction from the web
        Gets the flag from response body and sends it to GnssHandler

        :param MicroWebSrv._client http client: holds the client_connection
        :param MicroWebSrv._response http_response: holds the answer to the client
        """
        payload = await http_client.ReadRequestContentAsJSON()
        try:
            enable = payload["enabled"]
            print("NTRIP ENABLE: " + str(enable))
            if enable == True:
                cls._ntrip_stop_event.clear()
            if enable == False:
                cls._ntrip_stop_event.set()
            await http_response.WriteResponseOk()
        except Exception as ex:
            await http_response.WriteResponseJSONError(400)

    @classmethod
    async def _getSatSystems(cls, http_client, http_response):
        """
        ASYNC: Handles requests for the active satellite systems from the web
        Gets the active satellite systems from GnssHandler and sends it to client

        :param MicroWebSrv._client http client: holds the client_connection
        :param MicroWebSrv._response http_response: holds the answer to the client
        """
        try:
            sat_systems = await GnssHandler.get_satellite_systems()
            await http_response.WriteResponseJSONOk(sat_systems)
        except Exception as ex:
            await http_response.WriteResponseJSONError(400)

    @classmethod
    async def _setSatSystems(cls, http_client, http_response):
        """
        ASYNC: Handles config requests for setting the active satellite system from the web
        Gets the config from the request body and sends it to GnssHandler

        :param MicroWebSrv._client http client: holds the client_connection
        :param MicroWebSrv._response http_response: holds the answer to the client
        """
        payload = await http_client.ReadRequestContentAsJSON()
        try:
            gps = payload["gps"]
            glo = payload["glo"]
            gal = payload["gal"]
            bds = payload["bds"]
            resume_ntrip = False
            if not cls._ntrip_stop_event.is_set():  # if ntrip was running, stop ntrip and set a flag
                cls._ntrip_stop_event.set()
                resume_ntrip = True
            result = await GnssHandler.set_satellite_systems(gps, gal, glo, bds)
            await http_response.WriteResponseOk()
            if resume_ntrip:  # if flag was set, resume ntrip
                cls._ntrip_stop_event.clear()
        except Exception as ex:
            await http_response.WriteResponseJSONError(400)

    @classmethod
    async def _getNtripStatus(cls, http_client, http_response):
        """
        ASYNC: Handles requests for rtcm correction from the web
        Gets the rtcm flag from GnssHandler and sends it to client

        :param MicroWebSrv._client http client: holds the client_connection
        :param MicroWebSrv._response http_response: holds the answer to the client
        """
        try:
            enabled = None
            async with cls._rtcm_lock:
                if GnssHandler.rtcm_enabled:
                    enabled = True
                else:
                    enabled = False
            response = {"enabled": enabled}
            await http_response.WriteResponseJSONOk(response)
        except Exception as ex:
            await http_response.WriteResponseJSONError(400)


# Websocket
#--------------------------------------------------------------------------------------------

    @classmethod
    async def _getPosition(cls, http_client, http_response):
        """
        ASYNC: Polls real time position data from GnssHandler
        and sends it to the client

        :param MicroWebSrv._client http client: holds the client_connection
        :param MicroWebSrv._response http_response: holds the answer to the client
        """
        try:
            position = await GnssHandler.get_position()
            await http_response.WriteResponseJSONOk(position)
        except Exception as ex:
            await http_response.WriteResponseJSONError(400)

    @classmethod
    async def cb_receive_text(cls, webSocket, msg):
        """
        ASYNC: Dummy callback function needed by WebSocket Class
        Not in use!

        :param MicroWebSocket webSocket: the webSocket object
        :param str msg: message received over the webSocket
        """
        print("WS RECV TEXT : %s" % msg)
        await webSocket.SendText("Reply for %s" % msg)

    @classmethod
    async def cb_receive_binary(cls, webSocket, data):
        """
        ASYNC: Dummy callback function needed by WebSocket Class
        Not in use!

        :param MicroWebSocket webSocket: the webSocket object
        :param bytes msg: message received over the webSocket
        """
        print("WS RECV DATA : %s" % data)
        await uasyncio.sleep(1)

    @classmethod
    async def cb_closed(cls, webSocket):
        """
        ASYNC: Callback function which is called, when the webSocket
        connection closes
        Stops the position sending task

        :param MicroWebSocket webSocket: the webSocket object
        :param bytes msg: message received over the webSocket
        """
        print("WS CLOSED")
        cls._send_position_task.cancel()
        await uasyncio.sleep(1)

    @classmethod
    async def send_position(cls, websocket):
        """
        ASYNC: This function runs as task and send the real time
        position data over the webSocket

        :param MicroWebSocket webSocket: the webSocket object
        :param bytes msg: message received over the webSocket
        """
        position: PositionData
        accuracy: Accuracy
        realtime_message: RealTimeMessage
        rtcm: bool
        while not websocket.IsClosed():
            try:
                print("Sending Live Data")
                position = await GnssHandler.get_position() # Store data in dict
                accuracy = await GnssHandler.get_precision(False)
                rtcm = await GnssHandler.get_ntrip_status()
                realtime_message = RealTimeMessage(position, accuracy, rtcm)
                await websocket.SendText(str(ujson.dumps(realtime_message.__dict__)))  # Convert data to JSON and send
                print("Sended Live Data over Websocket")
            except Exception as ex:
                print(str(ex))
                websocket.Close()

        gc.collect()

    @classmethod
    async def cb_accept_ws(cls, webSocket, httpClient):
        """
        ASYNC: Callback function which is called, when a webSocket
        connection is established
        sets the other callback functions and starts the position transmitting task

        :param MicroWebSocket webSocket: the webSocket object
        :param bytes msg: message received over the webSocket
        """
        print("WS ACCEPT")
        webSocket.RecvTextCallback = cls.cb_receive_text
        webSocket.RecvBinaryCallback = cls.cb_receive_binary
        webSocket.ClosedCallback = cls.cb_closed
        cls._send_position_task = uasyncio.create_task(cls.send_position(webSocket))
