package de.hhn.roverclient

import android.content.Context
import android.content.pm.PackageManager
import android.os.AsyncTask
import android.os.Build
import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.os.Environment
import android.widget.Toast
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import com.google.android.material.bottomnavigation.BottomNavigationView
import de.hhn.roverclient.fragments.OsmFragment
import de.hhn.roverclient.fragments.SettingsFragment
import kotlinx.coroutines.*
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.InetAddress
import java.net.NetworkInterface
import java.net.URL
import java.nio.file.FileStore
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {


    private lateinit var osmFragment: OsmFragment
    private lateinit var settingsFragment: SettingsFragment
    var baseurl: String = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        AsyncTask.execute {
            var subnet = getSubnet()
            var ipList = scanLAN(subnet)
        }

        while (baseurl == "") {
            if (baseurl != "")
                break
        }
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val navView: BottomNavigationView = findViewById(R.id.bottom_nav_view)
        navView.setOnItemSelectedListener {
            when(it.itemId) {
                R.id.ic_osm_map -> replaceFragment(osmFragment)
                R.id.ic_settings -> replaceFragment(settingsFragment)
            }
            true
        }
        osmFragment = OsmFragment(baseurl)
        settingsFragment = SettingsFragment(baseurl)
        replaceFragment(osmFragment)
    }


    private fun replaceFragment(fragment: Fragment) {
        if(fragment != null) {
            val transaction = supportFragmentManager.beginTransaction()
            transaction.replace(R.id.fragment_container, fragment)
            transaction.commit()
        }
    }

    fun getSubnet(): String {
        val interfaces = NetworkInterface.getNetworkInterfaces()
        while (interfaces.hasMoreElements()) {
            val networkInterface = interfaces.nextElement()
            val addresses = networkInterface.inetAddresses
            while (addresses.hasMoreElements()) {
                val address = addresses.nextElement()
                if (address.isSiteLocalAddress) {
                    // The subnet is the first three octets of the address,
                    // followed by "0/24" to represent the subnet mask
                    val subnet = "${address.hostAddress.substring(0, address.hostAddress.lastIndexOf(".") + 1)}"
                    return subnet
                }
            }
        }
        return ""
    }

    // internal
    fun scanLAN(subnet: String){
        for (i in 99..149) {
            val address = "$subnet$i"
            val inetAddress = InetAddress.getByName(address)
            if (inetAddress.isReachable(100)) {
                baseurl = inetAddress.toString()
            }
        }
    }
}