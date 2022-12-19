"""
Global variables for gnss rtk rover.

Created on 2 Oct 2022

:author: vdueck
"""

# UART
UART1_TX = 0
UART1_RX = 1

BAUD_UART1 = 115200
BAUD_UART2 = 38400

# WiFi
WIFI_SSID = "gnss_rover_ap"
WIFI_PW = "ai_hhn_2022"
WIFI_CHECK_TIME = 10

# NTRIP
DEFAULT_BUFSIZE = 4096  # buffer size for NTRIP client
NTRIP_USER = ""
NTRIP_PW = ""
NTRIP_SERVER = ""
OUTPORT_NTRIP = 2101
MOUNTPOINT = ""
GGA_INTERVAL = 5
