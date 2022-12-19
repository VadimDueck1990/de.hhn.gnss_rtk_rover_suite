"""
PositionData class

Data Class, used to create RealTimeMessage objects
"""
class PositionData:

    def __init__(self, time, fixType, lat, lon, elev):
        self.time = time
        self.fixType = fixType
        self.lat = lat
        self.lon = lon
        self.elev = elev

"""
Accuracy class

Data Class, used to create RealTimeMessage objects
"""
class Accuracy:

    def __init__(self, hAcc, vAcc):
        self.hAcc = hAcc
        self.vAcc = vAcc

"""
RealTimeMessage class

Data Class for WebSocket transmission
"""
class RealTimeMessage:

    def __init__(self, positionData: PositionData, accuracy: Accuracy, rtcmEnabled: bool):
        self.exception = None
        self.time = positionData.time
        self.fixType = positionData.fixType
        self.lat = positionData.lat
        self.lon = positionData.lon
        self.elev = positionData.elev
        self.hAcc = accuracy.hAcc
        self.vAcc = accuracy.vAcc
        self.rtcmEnabled = rtcmEnabled