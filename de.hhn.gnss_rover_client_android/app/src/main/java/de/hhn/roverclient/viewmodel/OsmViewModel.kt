package de.hhn.roverclient.viewmodel

import android.os.Build
import android.os.Environment
import android.util.Log
import androidx.annotation.RequiresApi
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.gson.Gson
import de.hhn.roverclient.communication.SocketUpdate
import de.hhn.roverclient.communication.WebServicesProvider
import de.hhn.roverclient.models.PositionData
import de.hhn.roverclient.models.RealTimeMessage
import de.hhn.roverclient.models.UpdateRate
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.channels.consumeEach
import kotlinx.coroutines.launch
import okhttp3.*
import org.osmdroid.util.GeoPoint
import java.io.File
import java.io.FileOutputStream
import java.io.IOException
import java.math.BigDecimal
import java.math.RoundingMode
import java.net.InetAddress
import java.time.LocalTime
import java.time.ZonedDateTime
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit


class OsmViewModel constructor(
    private val interactor: OsmInteractor, private val baseurl: String):
    ViewModel() {

    companion object {
        lateinit var realTimeMessage: RealTimeMessage
    }

    // LiveData variables to update the UI
    var connectionStatus : MutableLiveData<String> = MutableLiveData()
    var fixType : MutableLiveData<String> = MutableLiveData()
    var time    : MutableLiveData<String> = MutableLiveData()
    var latency : MutableLiveData<String> = MutableLiveData()
    var lat     : MutableLiveData<String> = MutableLiveData()
    var lon     : MutableLiveData<String> = MutableLiveData()
    var elev    : MutableLiveData<String> = MutableLiveData()
    var hAcc    : MutableLiveData<String> = MutableLiveData()
    var vAcc    : MutableLiveData<String> = MutableLiveData()
    var rate    : MutableLiveData<String> = MutableLiveData()
    var rtcm    : MutableLiveData<String> = MutableLiveData()
    var location : MutableLiveData<GeoPoint> = MutableLiveData()
    var notification: MutableLiveData<String> = MutableLiveData()
    var recordToFile: Boolean = false


    @RequiresApi(Build.VERSION_CODES.O)
    fun subscribeToSocketEvents() {
        viewModelScope.launch(Dispatchers.IO) {
             try {
                interactor.startSocket().consumeEach {
                    if (it.exception == null) {
                        println(it.toString())
                        realTimeMessage = Gson().fromJson(it.text, RealTimeMessage::class.java) as RealTimeMessage
                        connectionStatus.postValue("Verbunden")
                        fixType.postValue(formatFixType(realTimeMessage.fixType))
                        time.postValue(formatTime(realTimeMessage.time))
                        latency.postValue(getLatency(realTimeMessage.time))
                        hAcc.postValue(formatAccuracy(realTimeMessage.hAcc))
                        vAcc.postValue(formatAccuracy(realTimeMessage.vAcc))
                        lat.postValue(formatLocation(realTimeMessage.lat))
                        lon.postValue(formatLocation(realTimeMessage.lon))
                        elev.postValue(formatElevation(realTimeMessage.elev))
                        rtcm.postValue(formatRtcm(realTimeMessage.rtcmEnabled))
                        location.postValue(formatGeoPoint(realTimeMessage.lat, realTimeMessage.lon))
                        println("inside websocket loop, file recording: " + recordToFile.toString())
                    } else {
                        onSocketError(it.exception)
                    }
                }
              } catch (ex: java.lang.Exception) {
                onSocketError(ex)
             }
        }
    }

    fun saveStringToFile(string: String) {
        try {
            val file = File(Environment.getExternalStorageDirectory(), "myFile.txt")
            if (!file.exists()) {
                file.createNewFile()
            }
            val fos = FileOutputStream(file)
            fos.write(string.toByteArray())
            fos.close()
            notification.postValue("Saving successful")
        } catch (e: Exception) {
            notification.postValue("Could not save File: " + e.toString())
            println("Could not save file, error: " + e.toString())
        }
    }


    private fun onSocketError(ex: Throwable) {
        resetAllFields()
        notification.postValue(ex.toString())
        println("Error occurred : ${ex.message}")
    }

    override fun onCleared() {
        interactor.stopSocket()
        super.onCleared()
    }

    fun getUpdateRate() {
        val url = "http://$baseurl/rate"
        val request = Request.Builder().url(url).build()
        val client = OkHttpClient()

        client.newCall(request).enqueue(object: Callback {
            override fun onFailure(call: Call, e: IOException) {
                rate.postValue("No Data available")
            }

            override fun onResponse(call: Call, response: Response) {
                try {
                    val result = Gson().fromJson(response.body?.string(), UpdateRate::class.java) as UpdateRate
                    val updateRate = result.updateRate
                    rate.postValue(updateRate.toString())

                }
                catch (ex: java.lang.Exception) {
                    onSocketError(ex)
                    rate.postValue("No Data available")
                }
            }
        })
    }

    private fun formatElevation(locationDM: String): String {
        if (locationDM == "") {
            return "No Data available"
        }
        else {
            var asDecimal = locationDM.toBigDecimal()
            val formatted = "%.2f".format(asDecimal)
            return formatted.toString()
        }
    }

    private fun formatRtcm(rtcmEnabled: Boolean): String {
        if (rtcmEnabled)
            return "Enabled"
        else
            return "Disabled"
    }

    private fun formatFixType(fixType: Int): String {
        when(fixType) {
            0 -> return "No fix"
            1 -> return "GPS Only"
            2 -> return "Differential GPS"
            3 -> return "PPS"
            4 -> return "RTK Fix"
            5 -> return "RTK Float"
            6 -> return "Dead Reckoning"
            7 -> return "Manual Input Mode"
            8 -> return "Simulation Mode"
            9 -> return "WAAS Fix"
            else -> return "No Data available"
        }
    }

    private fun formatAccuracy(accuracy: String): String {
        if(accuracy == "") {
            return "No Data available"
        }
        else {
            var acc = accuracy.toBigDecimal()
            var formattedAcc = acc.divide(BigDecimal(10.0))
            return formattedAcc.toString()
        }
    }
    @RequiresApi(Build.VERSION_CODES.O)
    private fun formatTime(timeString: String): String {
        if(timeString == "") {
            return "No Data available"
        }
        else {
            var inputFormatter = DateTimeFormatter.ofPattern("HHmmss.SS")
            var outputFormatter = DateTimeFormatter.ofPattern("HH:mm:ss.SS")
            var nmeaTime = LocalTime.parse(timeString, inputFormatter)
            var currentHour = ZonedDateTime.now().hour
            nmeaTime = nmeaTime.withHour(currentHour)
            var formattedTime = nmeaTime.format(outputFormatter)
            return formattedTime.toString()
        }
    }

    @RequiresApi(Build.VERSION_CODES.O)
    private fun getLatency(timeString: String): String {
        if(timeString == "") {
            return "No Data available"
        }
        else {
            var inputFormatter = DateTimeFormatter.ofPattern("HHmmss.SS")
            var outputFormatter = DateTimeFormatter.ofPattern("HH:mm:ss.SS")
            var nmeaTime = LocalTime.parse(timeString, inputFormatter)
            var currentHour = ZonedDateTime.now().hour
            nmeaTime = nmeaTime.withHour(currentHour)

            var latency = ChronoUnit.MILLIS.between(nmeaTime, LocalTime.now())
            return latency.toString()
        }
    }

    private fun formatGeoPoint(lat: String, lon: String): GeoPoint {
        if(lat == "")
            return GeoPoint(49.1218934023163, 9.20657878456699)
        else {
            var latDecimal = toDecimal(lat.toDouble())
            var lonDecimal = toDecimal(lon.toDouble())
            return GeoPoint(latDecimal, lonDecimal)
        }
    }

    private fun formatLocation(locationDM: String): String {
        if (locationDM == "") {
            return "No Data available"
        }
        else {
            var asDecimal = toDecimal(locationDM.toDouble())
            val formatted = "%.7f".format(asDecimal)
            return formatted.toString()
        }
    }

    private fun toDecimal(d: Double): Double {
        var bd = BigDecimal(d)
        bd = bd.movePointLeft(2)
        val degrees = getDegrees(d)
        val minutesAndSeconds = getMinutes(d)
        val decimal: BigDecimal = degrees.add(minutesAndSeconds).setScale(
            8,
            RoundingMode.HALF_EVEN
        )
        return decimal.toDouble()
    }
    private fun getMinutes(d: Double): BigDecimal {
        var bd = BigDecimal(d)
        bd = bd.movePointLeft(2)
        var minutesBd = bd.subtract(BigDecimal(bd.toInt()))
        minutesBd = minutesBd.movePointRight(2)
        return BigDecimal(
            minutesBd.toDouble() * 100 / 60
        ).movePointLeft(2)
    }

    private fun getDegrees(d: Double): BigDecimal {
        var bd = BigDecimal(d)
        bd = bd.movePointLeft(2)
        return BigDecimal(bd.toInt())
    }

    private fun resetAllFields() {
        connectionStatus.postValue("Nicht Verbunden")
        fixType.postValue("")
        time.postValue("")
        latency.postValue("")
        lat.postValue("")
        lon.postValue("")
        elev.postValue("")
        hAcc.postValue("")
        vAcc.postValue("")
        rtcm.postValue("")
    }

    @RequiresApi(Build.VERSION_CODES.O)
    private fun formatLogString(realTimeMessage: RealTimeMessage): String {
        var fixType = realTimeMessage.fixType.toString()
        var lat = formatLocation(realTimeMessage.lat)
        var lon = formatLocation(realTimeMessage.lon)
        var elev =formatLocation(realTimeMessage.lat)
        var time = formatTime(realTimeMessage.time)
        var latency = getLatency(realTimeMessage.time)

        var log = "$$fixType::$lat::$lon::$elev::$time::$latency"
        return log
    }
}

class OsmInteractor constructor(private val repository: OsmRepository) {

    fun stopSocket() {
        repository.closeSocket()
    }

    fun startSocket(): Channel<SocketUpdate> = repository.startSocket()
}

class OsmRepository constructor(private val webServicesProvider: WebServicesProvider) {

    fun startSocket(): Channel<SocketUpdate> =
        webServicesProvider.startSocket()

    fun closeSocket() {
        webServicesProvider.stopSocket()
    }
}