package de.hhn.roverclient.models

data class PositionData(var time: String,
                       var lat: String,
                       var lon: String,
                       var elev: String,
                       var fixType: Int)

data class Accuracy( var hAcc: String, var vAcc: String)

data class UpdateRate(var updateRate: Int)
data class Ntrip(var enabled: Boolean)

data class SatSystems(var bds: Int, var gps: Int, var glo: Int, var gal: Int)

data class RealTimeMessage(var exception: String,
                            var time: String,
                            var fixType: Int,
                            var lat: String,
                            var lon: String,
                            var elev: String,
                            var hAcc: String,
                            var vAcc: String,
                            var rtcmEnabled: Boolean)
