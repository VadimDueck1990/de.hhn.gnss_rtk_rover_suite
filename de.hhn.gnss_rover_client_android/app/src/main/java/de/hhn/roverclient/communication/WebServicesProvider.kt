package de.hhn.roverclient.communication

import de.hhn.roverclient.viewmodel.OsmInteractor
import kotlinx.coroutines.channels.Channel
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import java.util.concurrent.TimeUnit

class WebServicesProvider constructor(
    private val urlstring: String
)
{

    private var _webSocket: WebSocket? = null

    private val socketOkHttpClient = OkHttpClient.Builder()
        .readTimeout(30, TimeUnit.SECONDS)
        .connectTimeout(39, TimeUnit.SECONDS)
        .hostnameVerifier { _, _ -> true }
        .build()

    private var _webSocketListener: PositionWebSocketListener? = null

    fun startSocket(): Channel<SocketUpdate> =
        with(PositionWebSocketListener()) {
            startSocket(this)
            this@with.socketEventChannel
        }

    private fun startSocket(webSocketListener: PositionWebSocketListener) {
        _webSocketListener = webSocketListener
        println("INSIDE WEBServiceProvider: url " + urlstring)
        _webSocket = socketOkHttpClient.newWebSocket(
            Request.Builder().url(urlstring).build(),
            webSocketListener
        )
        socketOkHttpClient.dispatcher.executorService.shutdown()
    }

    fun stopSocket() {
        try {
            println("WEBSERVICEPROVIDER, CLOSING SOCKET")
            var result = _webSocket?.close(NORMAL_CLOSURE_STATUS, null)
            _webSocket = null
            _webSocketListener = null
        } catch (ex: Exception) {
        }
    }

    companion object {
        const val NORMAL_CLOSURE_STATUS = 1000
    }

}