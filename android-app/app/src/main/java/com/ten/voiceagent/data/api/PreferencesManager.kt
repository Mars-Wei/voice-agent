package com.ten.voiceagent.data.api

import android.content.Context
import android.content.SharedPreferences

/**
 * Manager for storing and retrieving user preferences like server IP and port.
 */
object PreferencesManager {
    private const val PREFS_NAME = "voice_agent_prefs"
    private const val KEY_SERVER_IP = "server_ip"
    private const val KEY_SERVER_PORT = "server_port"

    private const val DEFAULT_IP = "10.1.130.133"
    private const val DEFAULT_PORT = "8080"

    private lateinit var prefs: SharedPreferences

    /**
     * Initialize the preferences. Should be called once at app startup.
     */
    fun init(context: Context) {
        prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    var serverIp: String
        get() = prefs.getString(KEY_SERVER_IP, DEFAULT_IP) ?: DEFAULT_IP
        set(value) = prefs.edit().putString(KEY_SERVER_IP, value).apply()

    var serverPort: String
        get() = prefs.getString(KEY_SERVER_PORT, DEFAULT_PORT) ?: DEFAULT_PORT
        set(value) = prefs.edit().putString(KEY_SERVER_PORT, value).apply()

    /**
     * Returns the full server URL.
     */
    fun getServerUrl(): String = "http://$serverIp:$serverPort/"

    /**
     * Reset to default values.
     */
    fun resetToDefault() {
        serverIp = DEFAULT_IP
        serverPort = DEFAULT_PORT
    }
}
