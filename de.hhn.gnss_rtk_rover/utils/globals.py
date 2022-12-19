"""
Global variables for gnss rtk rover.

Created on 2 Oct 2022

:author: vdueck
"""

# UART
UART1_TX = 0
UART1_RX = 1

# # WiFi
# WIFI_SSID = "WLAN-L45XAB"
# WIFI_PW = "7334424916822832"
WIFI_SSID = "gnss_rover_ap"
WIFI_PW = "ai_hhn_2022"
WIFI_CHECK_TIME = 5

# NTRIP
DEFAULT_BUFSIZE = 4096  # buffer size for NTRIP client
NTRIP_USER = "HHN1"
NTRIP_PW = "sap21hhN"
NTRIP_SERVER = "sapos-ntrip.rlp.de"
OUTPORT_NTRIP = 2101
MOUNTPOINT = "VRS_3_4G_RP"
GGA_INTERVAL = 5
