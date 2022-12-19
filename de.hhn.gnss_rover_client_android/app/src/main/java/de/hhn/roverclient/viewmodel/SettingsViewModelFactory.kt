package de.hhn.roverclient.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.CreationExtras
import de.hhn.roverclient.communication.WebServicesProvider

class SettingsViewModelFactory(private val baseurl: String)
    : ViewModelProvider.NewInstanceFactory() {

    override fun <T : ViewModel> create(modelClass: Class<T>, extras: CreationExtras): T {
        return SettingsViewModel(baseurl) as T
    }
}