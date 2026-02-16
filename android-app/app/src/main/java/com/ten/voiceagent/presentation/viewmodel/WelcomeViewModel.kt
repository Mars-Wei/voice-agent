package com.ten.voiceagent.presentation.viewmodel

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ten.voiceagent.data.api.ApiClient
import com.ten.voiceagent.data.repository.ChatRepository
import com.ten.voiceagent.domain.model.AgentConfig
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStream
import java.net.HttpURLConnection
import java.net.URL
import javax.inject.Inject

/**
 * UI State for the Welcome screen.
 */
data class WelcomeUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val config: AgentConfig? = null
)

/**
 * ViewModel for the Welcome screen.
 * Matches web端的 implementation - auto-generates channel and userId.
 *
 * Flow:
 * 1. User taps connect button
 * 2. ViewModel generates random channel + userId (or uses saved values)
 * 3. ViewModel calls repository to start agent
 * 4. Navigation happens automatically when config is ready
 */
@HiltViewModel
class WelcomeViewModel @Inject constructor(
    private val chatRepository: ChatRepository
) : ViewModel() {

    private val TAG = "WelcomeViewModel"

    private val _uiState = MutableStateFlow(WelcomeUiState())
    val uiState: StateFlow<WelcomeUiState> = _uiState.asStateFlow()

    /**
     * Connect to the voice agent service.
     * Uses simple HttpURLConnection for testing.
     */
    fun connect() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }

            try {
                // Generate config with random channel and userId (matches web端)
                val config = AgentConfig.createDefault()
                Log.d(TAG, "Generated config: channel=${config.channel}, userId=${config.userId}")

                // Use simple HttpURLConnection for testing
                val result = testStartAgent(config)
                Log.d(TAG, "API result: $result")

                if (result.startsWith("Success:")) {
                    _uiState.update { it.copy(isLoading = false, config = config) }
                } else {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            error = result
                        )
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Connection error: ${e.message}", e)
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = "连接错误: ${e.message}"
                    )
                }
            }
        }
    }

    private suspend fun testStartAgent(config: AgentConfig): String = withContext(Dispatchers.IO) {
        try {
            val serverUrl = ApiClient.BASE_URL.removeSuffix("/")
            val url = URL("$serverUrl/start")
            val connection = url.openConnection() as HttpURLConnection
            connection.requestMethod = "POST"
            connection.setRequestProperty("Content-Type", "application/json")
            connection.doOutput = true
            connection.connectTimeout = 30000
            connection.readTimeout = 30000

            val json = """{"request_id":"test","channel_name":"${config.channel}","graph_name":"${config.graphName}","language":"${config.language}","voice_type":"${config.voiceType}","user_uid":${config.userId}}"""
            Log.d(TAG, "Sending request: $json")

            val outputStream = connection.outputStream
            outputStream.write(json.toByteArray(Charsets.UTF_8))
            outputStream.flush()
            outputStream.close()

            val responseCode = connection.responseCode
            val response = connection.inputStream.bufferedReader().readText()
            Log.d(TAG, "Response: $responseCode - $response")

            if (responseCode == 200 && response.contains("\"code\":\"0\"")) {
                "Success: Agent started"
            } else {
                "Failed: $responseCode - $response"
            }
        } catch (e: Exception) {
            Log.e(TAG, "API error: ${e.message}", e)
            "Error: ${e.message}"
        }
    }

    /**
     * Clear any error message.
     */
    fun clearError() {
        _uiState.update { it.copy(error = null) }
    }
}
