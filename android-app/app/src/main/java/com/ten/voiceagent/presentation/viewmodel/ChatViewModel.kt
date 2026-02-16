package com.ten.voiceagent.presentation.viewmodel

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ten.voiceagent.data.repository.ChatRepository
import com.ten.voiceagent.domain.model.AgoraTokenResponse
import com.ten.voiceagent.domain.model.AgentConfig
import com.ten.voiceagent.domain.model.ChatItem
import com.ten.voiceagent.domain.model.ChatMessage
import com.ten.voiceagent.domain.model.ConnectionState
import com.ten.voiceagent.domain.model.MessageDataType
import com.ten.voiceagent.domain.model.MessageRole
import com.ten.voiceagent.domain.model.MessageStatus
import com.ten.voiceagent.manager.AgoraRtcManager
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

/**
 * UI State for the Chat screen.
 */
data class ChatUiState(
    val isConnected: Boolean = false,
    val isLoading: Boolean = false,
    val isListening: Boolean = false,
    val isMicrophoneEnabled: Boolean = true,
    val isSpeaking: Boolean = false,
    val audioVolume: Int = 0,
    val messages: List<ChatItem> = emptyList(),
    val inputText: String = "",
    val connectionState: ConnectionState = ConnectionState.DISCONNECTED,
    val error: String? = null,
    val agentName: String = "AI Assistant"
)

/**
 * ViewModel for the Chat screen.
 * Manages chat state, Agora connections, and message handling.
 * Compatible with voice-assistant-with-memU message format.
 */
@HiltViewModel
class ChatViewModel @Inject constructor(
    private val chatRepository: ChatRepository,
    private val rtcManager: AgoraRtcManager
) : ViewModel() {

    private val TAG = "ChatViewModel"

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    private val _navigationEvent = MutableSharedFlow<NavigationEvent>()
    val navigationEvent: SharedFlow<NavigationEvent> = _navigationEvent.asSharedFlow()

    // Message buffer for streaming responses
    private val messageBuffer = mutableMapOf<String, ChatItem>()

    // Store current agent config
    private var currentConfig: AgentConfig? = null

    init {
        observeRtcState()
        observeRtcMessages()
        observeAudioVolume()
    }

    /**
     * Observe RTC connection state.
     */
    private fun observeRtcState() {
        viewModelScope.launch {
            rtcManager.connectionState.collect { state ->
                _uiState.update { it.copy(connectionState = state) }
                Log.d(TAG, "RTC connection state: $state")
            }
        }
    }

    /**
     * Observe incoming RTC data channel messages.
     */
    private fun observeRtcMessages() {
        viewModelScope.launch {
            rtcManager.dataMessageReceived.collect { message ->
                Log.d(TAG, "Received RTC data message: ${message.data}")
                handleIncomingMessage(message.data)
            }
        }
    }

    /**
     * Observe audio volume for visualization.
     */
    private fun observeAudioVolume() {
        viewModelScope.launch {
            rtcManager.audioVolume.collect { volume ->
                _uiState.update { it.copy(audioVolume = volume) }
            }
        }
    }

    /**
     * Handle incoming message from RTC data channel.
     * Parses voice-assistant-with-memU format:
     * {
     *   "data_type": "transcribe",
     *   "role": "user" | "assistant",
     *   "text": "...",
     *   "is_final": true/false
     * }
     */
    private fun handleIncomingMessage(data: String) {
        val chatMessage = ChatMessage.fromJson(data)
        if (chatMessage == null) {
            Log.w(TAG, "Failed to parse message: $data")
            return
        }

        when (chatMessage.dataType) {
            MessageDataType.TRANSCRIBE -> {
                handleTranscribeMessage(chatMessage)
            }
            MessageDataType.ASR_RESULT -> {
                // ASR results are from user's speech, ignore for chat display
                Log.d(TAG, "ASR result: ${chatMessage.text}")
            }
            MessageDataType.RAW -> {
                handleRawMessage(chatMessage)
            }
        }
    }

    private fun handleTranscribeMessage(message: ChatMessage) {
        val isUser = message.role == MessageRole.USER
        val currentTime = System.currentTimeMillis()

        if (message.isFinal) {
            // Final message, add to list
            val chatItem = ChatItem(
                id = message.id,
                text = message.text,
                isUser = isUser,
                timestamp = currentTime,
                status = MessageStatus.Delivered
            )
            _uiState.update { state ->
                state.copy(messages = state.messages + chatItem)
            }
            messageBuffer.remove(message.id)
        } else {
            // Streaming message, update buffer
            val existingItem = messageBuffer[message.id]
            if (existingItem != null) {
                val updatedItem = existingItem.copy(text = message.text)
                messageBuffer[message.id] = updatedItem
                _uiState.update { state ->
                    val updatedMessages = state.messages.map {
                        if (it.id == message.id) updatedItem else it
                    }
                    state.copy(messages = updatedMessages)
                }
            } else {
                // New streaming message
                val chatItem = ChatItem(
                    id = message.id,
                    text = message.text,
                    isUser = isUser,
                    timestamp = currentTime,
                    status = MessageStatus.Sending
                )
                messageBuffer[message.id] = chatItem
                _uiState.update { state ->
                    state.copy(messages = state.messages + chatItem)
                }
            }
        }

        // Update speaking state for assistant messages
        if (!isUser && !message.isFinal) {
            _uiState.update { it.copy(isSpeaking = true) }
        } else if (!isUser && message.isFinal) {
            _uiState.update { it.copy(isSpeaking = false) }
        }
    }

    private fun handleRawMessage(message: ChatMessage) {
        // Handle raw messages (e.g., reasoning content)
        if (message.isReasoning) {
            val chatItem = ChatItem(
                id = message.id,
                text = message.text,
                isUser = false,
                timestamp = System.currentTimeMillis(),
                status = MessageStatus.Delivered
            )
            _uiState.update { state ->
                state.copy(messages = state.messages + chatItem)
            }
        }
    }

    /**
     * Connect to the voice agent service.
     * Note: startAgent is skipped because WelcomeViewModel already started it.
     */
    fun connect(config: AgentConfig) {
        currentConfig = config
        viewModelScope.launch {
            Log.d(TAG, "Connecting to RTC: ${config.channel}")
            _uiState.update { it.copy(isLoading = true, error = null) }

            try {
                // Get Agora token (skip startAgent - already done by WelcomeViewModel)
                val tokenResponse = chatRepository.getAgoraToken(config.channel, config.userId)
                    .onFailure { error ->
                        Log.e(TAG, "Failed to get Agora token: ${error.message}")
                        _uiState.update {
                            it.copy(isLoading = false, error = "Failed to get Agora token: ${error.message}")
                        }
                        return@onFailure
                    }
                    .getOrNull()!!

                // Initialize and join RTC
                rtcManager.initialize(tokenResponse.appId)
                    .onFailure { error ->
                        Log.e(TAG, "Failed to initialize RTC: ${error.message}")
                        _uiState.update {
                            it.copy(isLoading = false, error = "Failed to initialize RTC: ${error.message}")
                        }
                        return@onFailure
                    }

                rtcManager.joinChannel(tokenResponse.token, config.channel, config.userId)
                    .onFailure { error ->
                        Log.e(TAG, "Failed to join RTC channel: ${error.message}")
                        _uiState.update {
                            it.copy(isLoading = false, error = "Failed to join RTC channel: ${error.message}")
                        }
                        return@onFailure
                    }

                // Connection successful
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        isConnected = true,
                        isListening = true,
                        isMicrophoneEnabled = true
                    )
                }

                Log.d(TAG, "Connected successfully")

            } catch (e: Exception) {
                Log.e(TAG, "Connection error: ${e.message}")
                _uiState.update {
                    it.copy(isLoading = false, error = "Connection error: ${e.message}")
                }
            }
        }
    }

    /**
     * Disconnect from the voice agent service.
     */
    fun disconnect() {
        viewModelScope.launch {
            val channelName = currentConfig?.channel ?: return@launch
            Log.d(TAG, "Disconnecting from agent: $channelName")
            rtcManager.leaveChannel()
            chatRepository.stopAgent(channelName)
            currentConfig = null
            messageBuffer.clear()

            _uiState.update { ChatUiState() }
            _navigationEvent.emit(NavigationEvent.NavigateToWelcome)
        }
    }

    /**
     * Update the text input field.
     */
    fun updateInputText(text: String) {
        _uiState.update { it.copy(inputText = text) }
    }

    /**
     * Send a text message.
     * Sends via RTC data channel in voice-assistant-with-memU format.
     */
    fun sendMessage() {
        val text = _uiState.value.inputText.trim()
        if (text.isBlank()) return

        viewModelScope.launch {
            // Add user message to the local list
            val messageId = UUID.randomUUID().toString()
            val userMessage = ChatItem(
                id = messageId,
                text = text,
                isUser = true,
                status = MessageStatus.Sending
            )
            _uiState.update { state ->
                state.copy(messages = state.messages + userMessage, inputText = "")
            }

            // Send via RTC data channel
            rtcManager.sendChatMessage(
                text = text,
                role = "user",
                isFinal = true,
                streamId = rtcManager.getCurrentUid()
            )
                .onSuccess {
                    _uiState.update { state ->
                        val updatedMessages = state.messages.map { msg ->
                            if (msg.id == messageId) msg.copy(status = MessageStatus.Sent)
                            else msg
                        }
                        state.copy(messages = updatedMessages)
                    }
                    Log.d(TAG, "Message sent successfully")
                }
                .onFailure { error ->
                    _uiState.update { state ->
                        val updatedMessages = state.messages.map { msg ->
                            if (msg.id == messageId) msg.copy(status = MessageStatus.Error)
                            else msg
                        }
                        state.copy(messages = updatedMessages)
                    }
                    Log.e(TAG, "Failed to send message: ${error.message}")
                }
        }
    }

    /**
     * Toggle microphone on/off.
     */
    fun toggleMicrophone() {
        val isEnabled = !_uiState.value.isMicrophoneEnabled
        rtcManager.enableLocalAudio(isEnabled)
        _uiState.update {
            it.copy(
                isMicrophoneEnabled = isEnabled,
                isListening = isEnabled
            )
        }
        Log.d(TAG, "Microphone ${if (isEnabled) "enabled" else "disabled"}")
    }

    /**
     * Toggle speakerphone on/off.
     */
    fun toggleSpeakerphone() {
        val shouldEnableSpeaker = _uiState.value.isMicrophoneEnabled
        rtcManager.setSpeakerphoneEnabled(shouldEnableSpeaker)
    }

    /**
     * Clear error message.
     */
    fun clearError() {
        _uiState.update { it.copy(error = null) }
    }

    override fun onCleared() {
        super.onCleared()
        Log.d(TAG, "ViewModel cleared, releasing resources")
        currentConfig = null
        rtcManager.release()
    }

    /**
     * Navigation events for the chat screen.
     */
    sealed class NavigationEvent {
        data object NavigateToWelcome : NavigationEvent()
    }
}
