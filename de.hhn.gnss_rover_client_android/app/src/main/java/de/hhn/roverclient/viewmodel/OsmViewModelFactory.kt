package de.hhn.roverclient.viewmodel

import android.os.AsyncTask
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.CreationExtras
import de.hhn.roverclient.communication.WebServicesProvider
import java.net.InetAddress

class OsmViewModelFactory(private val baseurl: String)
    : ViewModelProvider.NewInstanceFactory() {

    lateinit var webServicesProvider: WebServicesProvider
    lateinit var osmRepository: OsmRepository
    lateinit var osmInteractor: OsmInteractor

    override fun <T : ViewModel> create(modelClass: Class<T>, extras: CreationExtras): T {

        webServicesProvider = WebServicesProvider("ws://$baseurl/")
        println("WEBSOCKET URL: " + "ws://$baseurl/")
        osmRepository = OsmRepository(webServicesProvider)
        osmInteractor = OsmInteractor(osmRepository)
        return OsmViewModel(osmInteractor, baseurl) as T
    }


}