package de.hhn.roverclient.fragments


import android.os.Bundle
import androidx.fragment.app.Fragment
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.CheckBox
import android.widget.Switch
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.widget.SwitchCompat
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.core.os.bundleOf
import androidx.fragment.app.setFragmentResult
import androidx.lifecycle.Observer
import androidx.lifecycle.ViewModelProvider
import com.google.android.material.textfield.TextInputEditText
import de.hhn.roverclient.R
import de.hhn.roverclient.models.SatSystems
import de.hhn.roverclient.viewmodel.OsmViewModel
import de.hhn.roverclient.viewmodel.OsmViewModelFactory
import de.hhn.roverclient.viewmodel.SettingsViewModel
import de.hhn.roverclient.viewmodel.SettingsViewModelFactory

// TODO: Rename parameter arguments, choose names that match
// the fragment initialization parameters, e.g. ARG_ITEM_NUMBER
private const val ARG_PARAM1 = "param1"
private const val ARG_PARAM2 = "param2"

/**
 * A simple [Fragment] subclass.
 * Use the [SettingsFragment.newInstance] factory method to
 * create an instance of this fragment.
 */
class SettingsFragment constructor(
    private val baseurl: String
) : Fragment() {

    lateinit var viewModel: SettingsViewModel
    lateinit var rootView: View
    lateinit var settingsViewModelFactory: SettingsViewModelFactory

    private lateinit var cbGpsEnabled: CheckBox
    private lateinit var cbGloEnabled: CheckBox
    private lateinit var cbGalEnabled: CheckBox
    private lateinit var cbBdsEnabled: CheckBox
    private lateinit var btnSetSatSystems: Button
    private lateinit var swRtcmEnable: SwitchCompat
    private lateinit var tiRate: TextInputEditText
    private lateinit var btnRate: Button
    private lateinit var swFileRecordingEnabled: SwitchCompat

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        // Inflate the layout for this fragment
        rootView = inflater.inflate(R.layout.fragment_settings, container, false)

        cbGpsEnabled =rootView.findViewById(R.id.cb_gps)
        cbGloEnabled =rootView.findViewById(R.id.cb_glonass)
        cbGalEnabled =rootView.findViewById(R.id.cb_galileo)
        cbBdsEnabled =rootView.findViewById(R.id.cb_bds)
        btnSetSatSystems = rootView.findViewById(R.id.set_sat_systems_btn)
        swRtcmEnable = rootView.findViewById(R.id.rtcm_switch)
        btnRate = rootView.findViewById(R.id.update_rate_btn)
        tiRate = rootView.findViewById(R.id.ip_input_field_text)
        swFileRecordingEnabled = rootView.findViewById(R.id.file_record_switch)

        settingsViewModelFactory = SettingsViewModelFactory(baseurl)
        viewModel = ViewModelProvider(this, settingsViewModelFactory).get(SettingsViewModel::class.java)

        viewModel.notifications.observe(viewLifecycleOwner, Observer {
            Toast.makeText(this.context, it, Toast.LENGTH_SHORT).show()
        })
        viewModel.GpsEnabled.observe(viewLifecycleOwner, Observer {
            cbGpsEnabled.isChecked = it
        })
        viewModel.GlonassEnabled.observe(viewLifecycleOwner, Observer {
            cbGloEnabled.isChecked = it
        })
        viewModel.GalileoEnabled.observe(viewLifecycleOwner, Observer {
            cbGalEnabled.isChecked = it
        })
        viewModel.BdsEnabled.observe(viewLifecycleOwner, Observer {
            cbBdsEnabled.isChecked = it
        })
        viewModel.RtcmEnabled.observe(viewLifecycleOwner, Observer {
            swRtcmEnable.isChecked = it
        })

        btnSetSatSystems.setOnClickListener{
            var bds = if (cbBdsEnabled.isChecked) 1 else 0
            var gps = if (cbGpsEnabled.isChecked) 1 else 0
            var glo = if (cbGloEnabled.isChecked) 1 else 0
            var gal = if (cbGalEnabled.isChecked) 1 else 0

            if (checkMinSatSystems())
                viewModel.setSatsystems(bds, gps, glo, gal)
            else
                Toast.makeText(this.context, "Bitte aktivieren Sie mindestens 1 Satellitensystem", Toast.LENGTH_SHORT).show()
        }

        swRtcmEnable.setOnCheckedChangeListener{_, isChecked ->
            viewModel.setRtcm(isChecked)
        }

        btnRate.setOnClickListener{
            try {
                var rate = tiRate.text.toString()
                var urate = rate.toInt()
                viewModel.setUpdateRate(urate)
            }
            catch (ex: Exception) {
                Toast.makeText(this.context, "Bitte geben Sie eine Zahl 50 - 5000 an", Toast.LENGTH_SHORT).show()
            }
        }

        swFileRecordingEnabled.setOnCheckedChangeListener{_, isChecked ->
            val recordingEnabled = isChecked
            setFragmentResult("requestKey", bundleOf("bundleKey" to recordingEnabled))
        }
        viewModel.getSatsystems()
        viewModel.getRtcm()

        return rootView
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        rootView = view
        checkMinSatSystems()
        // obtain ViewModel
    }

    private fun checkMinSatSystems(): Boolean{
        var numOfActiveSystems = 0
        if (cbBdsEnabled.isChecked) numOfActiveSystems++
        if (cbGpsEnabled.isChecked) numOfActiveSystems++
        if (cbGloEnabled.isChecked) numOfActiveSystems++
        if (cbGalEnabled.isChecked) numOfActiveSystems++
        return numOfActiveSystems != 0
    }
}