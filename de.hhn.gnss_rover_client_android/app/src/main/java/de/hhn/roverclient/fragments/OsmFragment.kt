package de.hhn.roverclient.fragments

import android.content.SharedPreferences
import android.os.Build
import android.os.Bundle
import android.preference.PreferenceManager
import android.util.DisplayMetrics
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import android.widget.Toast
import androidx.annotation.RequiresApi
import androidx.fragment.app.Fragment
import androidx.fragment.app.setFragmentResultListener
import androidx.lifecycle.Observer
import androidx.lifecycle.ViewModelProvider
import de.hhn.roverclient.R
import de.hhn.roverclient.viewmodel.OsmViewModel
import de.hhn.roverclient.viewmodel.OsmViewModelFactory
import org.osmdroid.api.IMapController
import org.osmdroid.config.Configuration.*
import org.osmdroid.tileprovider.tilesource.TileSourceFactory
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Marker
import org.osmdroid.views.overlay.ScaleBarOverlay
import org.osmdroid.views.overlay.compass.CompassOverlay
import org.osmdroid.views.overlay.compass.InternalCompassOrientationProvider


// TODO: Rename parameter arguments, choose names that match
// the fragment initialization parameters, e.g. ARG_ITEM_NUMBER
private const val ARG_PARAM1 = "param1"
private const val ARG_PARAM2 = "param2"

/**
 * A simple [Fragment] subclass.
 * Use the [OsmFragment.newInstance] factory method to
 * create an instance of this fragment.
 */
class OsmFragment constructor(
    private val baseurl: String
) : Fragment(R.layout.fragment_osm) {


    lateinit var viewModel: OsmViewModel
    lateinit var rootView: View
    lateinit var osmViewModelFactory: OsmViewModelFactory
    var fileRecordingEnabled: Boolean = false

    private lateinit var tvConnectionStatus: TextView
    private lateinit var tvFixtype: TextView
    private lateinit var tvTime: TextView
    private lateinit var tvLatency: TextView
    private lateinit var tvLatitude: TextView
    private lateinit var tvLongitude: TextView
    private lateinit var tvElevation: TextView
    private lateinit var tvHacc: TextView
    private lateinit var tvVacc: TextView
    private lateinit var tvRate: TextView
    private lateinit var tvRtcm: TextView
    /**
     * Companion
     * some static variables that are needed in the fragments
     */
    companion object{
        private lateinit var map : MapView
        private lateinit var mapController: IMapController
        private lateinit var geoLocation: GeoPoint
        private lateinit var positionMarker: Marker
        lateinit var prefs: SharedPreferences
    }


    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prefs = PreferenceManager.getDefaultSharedPreferences(this.context)
        // Use the Kotlin extension in the fragment-ktx artifact
        setFragmentResultListener("requestKey") { requestKey, bundle ->
            // We use a String here, but any type that can be put in a Bundle is supported
            val recordingEnabled = bundle.getBoolean("bundleKey")
            println("FILE RECORDING ENABLED: " + recordingEnabled.toString())
            // Do something with the result
        }

    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        getInstance().load(this.context, PreferenceManager.getDefaultSharedPreferences(this.context))
        // Inflate the layout for this fragment
        var osmView = inflater.inflate(R.layout.fragment_osm, container, false)

        tvConnectionStatus =osmView.findViewById(R.id.text_connection_status)
        tvFixtype = osmView.findViewById(R.id.text_fixtype)
        tvTime = osmView.findViewById(R.id.time_text)
        tvLatency = osmView.findViewById(R.id.latency_text)
        tvLatitude = osmView.findViewById(R.id.lat_text)
        tvLongitude = osmView.findViewById(R.id.long_text)
        tvElevation = osmView.findViewById(R.id.elev_text)
        tvHacc = osmView.findViewById(R.id.hacc_text)
        tvVacc = osmView.findViewById(R.id.vac_text)
        tvRate = osmView.findViewById(R.id.text_updaterate)
        tvRtcm = osmView.findViewById(R.id.text_rtcmstatus)
        // init map
        initOsmMap(osmView)
        return osmView
    }

    @RequiresApi(Build.VERSION_CODES.O)
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        println("BASEURL IN FRAGMENT = " + baseurl)
        rootView = view
        // obtain ViewModel
        osmViewModelFactory = OsmViewModelFactory(baseurl)
        viewModel = ViewModelProvider(this, osmViewModelFactory).get(OsmViewModel::class.java)

        viewModel.notification.observe(viewLifecycleOwner, Observer {
            Toast.makeText(this.context, it, Toast.LENGTH_SHORT).show()
        })
        viewModel.location.observe(viewLifecycleOwner, Observer {
            geoLocation = it
            mapController.setCenter(geoLocation);
            positionMarker.setPosition(geoLocation);
            map.getOverlays().add(positionMarker);
        })
        viewModel.connectionStatus.observe(viewLifecycleOwner, Observer {
            tvConnectionStatus.text = it.toString()
        })
        viewModel.fixType.observe(viewLifecycleOwner, Observer {
            tvFixtype.text = it.toString()
        })
        viewModel.time.observe(viewLifecycleOwner, Observer {
            tvTime.text = it.toString()
        })
        viewModel.latency.observe(viewLifecycleOwner, Observer {
            tvLatency.text = it.toString()
        })
        viewModel.lat.observe(viewLifecycleOwner, Observer {
            tvLatitude.text = it.toString()
        })
        viewModel.lon.observe(viewLifecycleOwner, Observer {
            tvLongitude.text = it.toString()
        })
        viewModel.elev.observe(viewLifecycleOwner, Observer {
            tvElevation.text = it.toString()
        })

        viewModel.hAcc.observe(viewLifecycleOwner, Observer {
            tvHacc.text = it.toString()
        })
        viewModel.vAcc.observe(viewLifecycleOwner, Observer {
            tvVacc.text = it.toString()
        })
        viewModel.rate.observe(viewLifecycleOwner, Observer {
            tvRate.text = it.toString()
        })
        viewModel.rtcm.observe(viewLifecycleOwner, Observer {
            tvRtcm.text = it.toString()
        })
        viewModel.recordToFile = fileRecordingEnabled

        viewModel.subscribeToSocketEvents()
        viewModel.getUpdateRate()
    }

    override fun onResume() {
        super.onResume()
        //this will refresh the osmdroid configuration on resuming.
        //if you make changes to the configuration, use
        //SharedPreferences prefs = PreferenceManager.getDefaultSharedPreferences(this);
        //Configuration.getInstance().load(this, PreferenceManager.getDefaultSharedPreferences(this));
        map.onResume() //needed for compass, my location overlays, v6.0.0 and up
    }

    override fun onPause() {
        super.onPause()
        //this will refresh the osmdroid configuration on resuming.
        //if you make changes to the configuration, use
        //SharedPreferences prefs = PreferenceManager.getDefaultSharedPreferences(this);
        //Configuration.getInstance().save(this, prefs);
        map.onPause()  //needed for compass, my location overlays, v6.0.0 and up
    }


    fun initOsmMap(view: View) {
        map = view.findViewById(R.id.osm_map)
        map.setTileSource(TileSourceFactory.MAPNIK)
        map.setUseDataConnection(true)
        mapController = map.controller
        mapController.setZoom(15.0)
        val startPoint = GeoPoint(50.3902913, 7.3161298);
        mapController.setCenter(startPoint);

        var compassOverlay = CompassOverlay(context, InternalCompassOrientationProvider(context), map)
        compassOverlay.enableCompass()
        map.overlays.add(compassOverlay)

        // to the non-activity class.
        val dm : DisplayMetrics = resources.displayMetrics
        val scaleBarOverlay = ScaleBarOverlay(map)
        scaleBarOverlay.setCentred(true)
        //play around with these values to get the location on screen in the right place for your application
        scaleBarOverlay.setScaleBarOffset(dm.widthPixels / 2, 10)
        map.overlays.add(scaleBarOverlay)

        var markerPoint = startPoint;
        positionMarker= Marker(map);
        positionMarker.setPosition(startPoint);
        positionMarker.setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM);
        map.getOverlays().add(positionMarker);
    }
}