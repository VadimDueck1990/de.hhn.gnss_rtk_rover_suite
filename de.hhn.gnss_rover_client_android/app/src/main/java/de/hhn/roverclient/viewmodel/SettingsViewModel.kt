package de.hhn.roverclient.viewmodel

import android.widget.Toast
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.google.gson.Gson
import de.hhn.roverclient.models.Ntrip
import de.hhn.roverclient.models.SatSystems
import de.hhn.roverclient.models.UpdateRate
import kotlinx.coroutines.MainScope
import okhttp3.*
import okhttp3.RequestBody.Companion.toRequestBody
import org.osmdroid.util.GeoPoint
import java.io.IOException

class SettingsViewModel constructor(private val baseurl: String)
    : ViewModel() {

    // LiveData variables to update the UI
    val webapiurl = "http://$baseurl"
    var notifications   : MutableLiveData<String> = MutableLiveData()
    var GpsEnabled      : MutableLiveData<Boolean> = MutableLiveData()
    var GlonassEnabled  : MutableLiveData<Boolean> = MutableLiveData()
    var GalileoEnabled  : MutableLiveData<Boolean> = MutableLiveData()
    var BdsEnabled      : MutableLiveData<Boolean> = MutableLiveData()
    var RtcmEnabled     : MutableLiveData<Boolean> = MutableLiveData()

    fun getSatsystems() {
        val url = webapiurl + "/satsystems"
        val request = Request.Builder().url(url).build()
        val client = OkHttpClient()

        client.newCall(request).enqueue(object: Callback {
            override fun onFailure(call: Call, e: IOException) {
                notifications.postValue("Satellitensysteme konnten nicht laden werden, etwas ist schief gegangen: " + e.toString())
            }

            override fun onResponse(call: Call, response: Response) {
                try {
                    val result = Gson().fromJson(response.body?.string(), SatSystems::class.java) as SatSystems
                    println("GET SAT SYSTEMS: " + result.toString())
                    if (result.bds == 0)
                        BdsEnabled.postValue(false)
                    else
                        BdsEnabled.postValue(true)
                    if (result.gps == 0)
                        GpsEnabled.postValue(false)
                    else
                        GpsEnabled.postValue(true)
                    if (result.glo == 0)
                        GlonassEnabled.postValue(false)
                    else
                        GlonassEnabled.postValue(true)
                    if (result.gal == 0)
                        GalileoEnabled.postValue(false)
                    else
                        GalileoEnabled.postValue(true)
                }
                catch (ex: java.lang.Exception) {
                    notifications.postValue("Satellitensysteme konnten nicht laden werden, etwas ist schief gegangen: " + ex.toString())
                }
            }
        })
    }

    fun setSatsystems(bds: Int, gps: Int, glo: Int, gal: Int) {
        var activeSystems = SatSystems(bds, gps, glo, gal)
        var payload = Gson().toJson(activeSystems)
        println("SET SAT SYSTEMS: " + payload.toString())
        var requestBody = payload.toRequestBody()

        val url = webapiurl + "/satsystems"
        val request = Request.Builder()
                        .method("POST", requestBody)
                        .url(url)
                        .build()

        val client = OkHttpClient()

        client.newCall(request).enqueue(object: Callback {
            override fun onFailure(call: Call, e: IOException) {
                notifications.postValue("Satellitensysteme konnten nicht gesetzt werden, etwas ist schief gegangen: " + e.toString())
            }

            override fun onResponse(call: Call, response: Response) {
                try {
                    val result = activeSystems
                    if (result.bds == 0)
                        BdsEnabled.postValue(false)
                    else
                        BdsEnabled.postValue(true)
                    if (result.gps == 0)
                        GpsEnabled.postValue(false)
                    else
                        GpsEnabled.postValue(true)
                    if (result.glo == 0)
                        GlonassEnabled.postValue(false)
                    else
                        GlonassEnabled.postValue(true)
                    if (result.gal == 0)
                        GalileoEnabled.postValue(false)
                    else
                        GalileoEnabled.postValue(true)
                    notifications.postValue("Satellitensysteme wurden erfolgreich gesetzt")
                }
                catch (ex: java.lang.Exception) {
                    notifications.postValue("Satellitensysteme konnten nicht gesetzt werden, etwas ist schief gegangen: " + ex.toString())
                }
            }
        })
    }

    fun getRtcm() {
        val url = webapiurl + "/ntrip"
        val request = Request.Builder().url(url).build()
        val client = OkHttpClient()

        client.newCall(request).enqueue(object: Callback {
            override fun onFailure(call: Call, e: IOException) {
                notifications.postValue("RTCM Status konnte nicht abgefragt werden, etwas ist schief gelaufen: " + e.toString())
            }

            override fun onResponse(call: Call, response: Response) {
                try {
                    val result = Gson().fromJson(response.body?.string(), Ntrip::class.java) as Ntrip
                    println("GET RTCM: " + result.toString())
                    RtcmEnabled.postValue(result.enabled)
                }
                catch (ex: java.lang.Exception) {
                    notifications.postValue("RTCM Status konnte nicht abgefragt werden, etwas ist schief gelaufen: " + ex.toString())
                }
            }
        })
    }

    fun setRtcm(checked: Boolean) {
        var enableNtrip = Ntrip(checked)
        var payload = Gson().toJson(enableNtrip)
        println("SET NTRIP: " + payload.toString())
        var requestBody = payload.toRequestBody()

        val url = webapiurl + "/ntrip"
        val request = Request.Builder()
            .method("POST", requestBody)
            .url(url)
            .build()

        val client = OkHttpClient()

        client.newCall(request).enqueue(object: Callback {
            override fun onFailure(call: Call, e: IOException) {
                notifications.postValue("RTCM Status konnte nicht gesetzt werden, etwas ist schief gelaufen: " + e.toString())
            }

            override fun onResponse(call: Call, response: Response) {
                if (response.isSuccessful)
                    notifications.postValue("RTCM Status wurde erfolgreich gesetzt")
            }
        })
    }

    fun setUpdateRate(urate: Int) {
        var updateRate = UpdateRate(urate)
        var payload = Gson().toJson(updateRate)
        println("SET RATE: " + payload.toString())
        var requestBody = payload.toRequestBody()

        val url = webapiurl + "/rate"
        val request = Request.Builder()
            .method("POST", requestBody)
            .url(url)
            .build()

        val client = OkHttpClient()

        client.newCall(request).enqueue(object: Callback {
            override fun onFailure(call: Call, e: IOException) {
                notifications.postValue("Aktualisierungsrate konnte nicht gesetzt werden, etwas ist schief gelaufen: " + e.toString())
            }

            override fun onResponse(call: Call, response: Response) {
                if (response.isSuccessful)
                    notifications.postValue("Aktualisierungsrate wurde erfolgreich gesetzt")
            }
        })
    }
}