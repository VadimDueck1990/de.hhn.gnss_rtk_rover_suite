import gc

import uasyncio
from machine import UART, Pin
from uasyncio import Event, Lock
from utils.wifi_manager import WiFiManager
from utils.globals import WIFI_SSID, WIFI_PW, BAUD_UART1, BAUD_UART2
from utils.mem_debug import debug_gc
from gnss.gnss_handler import GnssHandler
from serial_communication.uart_writer import UartWriter
from utils.queue import Queue
from serial_communication.uart_reader import UartReader
from gnss.gnss_ntripclient import GNSSNTRIPClient
from web_api.request_handler import RequestHandler
gc.collect()


async def init():
    ntrip_stop_event = Event()
    ggaevent = Event()

    masterTx = Pin(0)
    masterRx = Pin(1)

    rtcmTx = Pin(4)
    rtcmRx = Pin(5)

    rtcm_enabled = False
    rtcm_lock = Lock()

    led = Pin("LED", Pin.OUT)


    gga_q = Queue(maxsize=1)
    cfg_q = Queue(maxsize=5)
    nav_q = Queue(maxsize=5)
    ack_q = Queue(maxsize=20)
    msg_q = Queue(maxsize=5)
    pos_q = Queue(maxsize=1)

    uart_rtcm = UART(1, BAUD_UART2, timeout=500)
    uart_rtcm.init(bits=8, parity=None, stop=1, tx=rtcmTx, rx=rtcmRx, rxbuf=4096, txbuf=4096)

    uart_ubx_nmea = UART(0, BAUD_UART1, timeout=500)
    uart_ubx_nmea.init(bits=8, parity=None, stop=1, tx=masterTx, rx=masterRx, rxbuf=8192, txbuf=4096)

    sreader = uasyncio.StreamWriter(uart_ubx_nmea)
    swriter = uasyncio.StreamReader(uart_ubx_nmea)
    test = ""

    UartWriter.initialize(app=test,
                          swriter=swriter,
                          queue=msg_q)
    UartReader.initialize(app=test,
                          sreader=sreader,
                          gga_q=gga_q,
                          cfg_resp_q=cfg_q,
                          nav_pvt_q=nav_q,
                          ack_nack_q=ack_q,
                          ggaevent=ggaevent,
                          position_q=pos_q)

    GnssHandler.initialize(app=test,
                           ack_nack_q=ack_q,
                           nav_pvt_q=nav_q,
                           cfg_resp_q=cfg_q,
                           msg_q=msg_q,
                           gga_q=gga_q,
                           pos_q=pos_q,
                           ntrip_lock=rtcm_lock,
                           stop_event=ntrip_stop_event)

    writertask = uasyncio.create_task(UartWriter.run())
    readertask = uasyncio.create_task(UartReader.run())

    await GnssHandler.set_minimum_nmea_msgs()
    wifi = WiFiManager(WIFI_SSID, WIFI_PW)
    await wifi.connect()
    debug_gc()
    # await GnssHandler.set_update_rate(2000)
    enabled = await GnssHandler.set_high_precision_mode(1)
    print("main -> high precision mode enabled: " + str(enabled))
    gc.collect()

    ntripclient = GNSSNTRIPClient(uart_rtcm, test, gga_q, ggaevent)
    ntriptask = uasyncio.create_task(ntripclient.run(rtcm_lock, ntrip_stop_event))
    gc.collect()
    gccount = 0
    webserver = uasyncio.create_task(RequestHandler.initialize(test, pos_q, ntrip_stop_event, rtcm_lock))
    while wifi.wifi.isconnected():
        led.toggle()
        # accuracy = await GnssHandler.get_precision(False)
        # print("hAcc: " + str(accuracy.hAcc) + "mm, vAcc: " + str(accuracy.vAcc) + "mm")
        # gccount += 1
        async with rtcm_lock:
            print("rtcm enabled: " + str(GnssHandler.rtcm_enabled))
        # debug_gc()
        await uasyncio.sleep(1)


def main():
    print("starting main")
    uasyncio.run(init())

main()


