package com.ten.voiceagent.data.api

import android.util.Log
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStream
import java.net.HttpURLConnection
import java.net.URL

/**
 * Simple network test utility.
 */
object NetworkTest {
    private const val TAG = "NetworkTest"

    /**
     * Test network connection to the server.
     */
    fun testConnection(serverUrl: String): String {
        return try {
            val url = URL("$serverUrl/graphs")
            val connection = url.openConnection() as HttpURLConnection
            connection.requestMethod = "GET"
            connection.connectTimeout = 10000
            connection.readTimeout = 10000

            val responseCode = connection.responseCode
            val response = connection.inputStream.bufferedReader().readText()

            Log.d(TAG, "Response code: $responseCode")
            Log.d(TAG, "Response: $response")

            "Success: $responseCode - $response"
        } catch (e: Exception) {
            Log.e(TAG, "Error: ${e.message}", e)
            "Error: ${e.message}"
        }
    }

    /**
     * Test POST request to start agent.
     */
    fun testStartAgent(serverUrl: String, channel: String): String {
        return try {
            val url = URL("$serverUrl/start")
            val connection = url.openConnection() as HttpURLConnection
            connection.requestMethod = "POST"
            connection.setRequestProperty("Content-Type", "application/json")
            connection.doOutput = true
            connection.connectTimeout = 30000
            connection.readTimeout = 30000

            val json = """{"request_id":"test","channel_name":"$channel","graph_name":"voice_assistant"}"""
            val outputStream: OutputStream = connection.outputStream
            outputStream.write(json.toByteArray())
            outputStream.flush()
            outputStream.close()

            val responseCode = connection.responseCode
            val response = connection.inputStream.bufferedReader().readText()

            Log.d(TAG, "Start agent response: $responseCode - $response")

            "Success: $responseCode - $response"
        } catch (e: Exception) {
            Log.e(TAG, "Start agent error: ${e.message}", e)
            "Error: ${e.message}"
        }
    }
}
