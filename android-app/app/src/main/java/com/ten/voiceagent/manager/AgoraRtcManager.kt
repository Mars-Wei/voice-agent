package com.ten.voiceagent.manager

import android.content.Context
import android.util.Log
import com.ten.voiceagent.domain.model.ConnectionState
import io.agora.rtc2.Constants
import io.agora.rtc2.DataStreamConfig
import io.agora.rtc2.IRtcEngineEventHandler
import io.agora.rtc2.RtcEngine
import io.agora.rtc2.RtcEngineConfig
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Data class representing a message received from RTC data channel.
 */
data class RtcDataMessage(
    val data: String,
    val streamId: Int,
    val timestamp: Long = System.currentTimeMillis()
)

/**
 * Manager for Agora RTC (Real-Time Communication) operations.
 * Compatible with Agora SDK 4.x.
 *
 * Supports:
 * - Audio streaming (microphone to cloud, cloud to speaker)
 * - Data channel messages (for chat/text messages)
 * - Audio volume indication
 */
@Singleton
class AgoraRtcManager @Inject constructor(
    private val context: Context
) {
    private val TAG = "AgoraRtcManager"
    private var rtcEngine: RtcEngine? = null

    private val _connectionState = MutableStateFlow(ConnectionState.DISCONNECTED)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()

    private val _audioVolume = MutableStateFlow(0)
    val audioVolume: StateFlow<Int> = _audioVolume.asStateFlow()

    private val _dataMessageReceived = MutableSharedFlow<RtcDataMessage>()
    val dataMessageReceived: SharedFlow<RtcDataMessage> = _dataMessageReceived.asSharedFlow()

    private val _remoteUserJoined = MutableSharedFlow<Int>()
    val remoteUserJoined: SharedFlow<Int> = _remoteUserJoined.asSharedFlow()

    private val _remoteUserLeft = MutableSharedFlow<Int>()
    val remoteUserLeft: SharedFlow<Int> = _remoteUserLeft.asSharedFlow()

    private var currentChannel: String? = null
    private var currentUid: Int = 0
    private var dataStreamId: Int = -1

    /**
     * Initialize the RTC engine with the given app ID.
     */
    fun initialize(appId: String): Result<Unit> {
        return try {
            val config = RtcEngineConfig()
            config.mContext = context
            config.mAppId = appId
            config.mEventHandler = createEventHandler()

            rtcEngine = RtcEngine.create(config)

            // Apply audio processing before enabling audio
            applyAudioProcessing()

            rtcEngine?.enableAudio()

            // Set audio scenario to CHATROOM for optimal voice quality with AEC
            // 0 = AUDIO_SCENARIO_DEFAULT
            // 1 = AUDIO_SCENARIO_CHATROOM_ENTERTAINMENT
            // 2 = AUDIO_SCENARIO_EDUCATION
            // 3 = AUDIO_SCENARIO_GAME_STREAMING
            // 4 = AUDIO_SCENARIO_HIGHQUALITY_STAR
            rtcEngine?.setAudioScenario(3) // GAME_STREAMING - best for AEC

            rtcEngine?.setChannelProfile(Constants.CHANNEL_PROFILE_COMMUNICATION)
            rtcEngine?.setAudioProfile(Constants.AUDIO_PROFILE_SPEECH_STANDARD)

            // Enable audio volume indication
            rtcEngine?.enableAudioVolumeIndication(100, 3, true)

            Result.success(Unit)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to initialize RTC: ${e.message}")
            Result.failure(e)
        }
    }

    /**
     * Apply comprehensive audio processing settings for echo cancellation.
     */
    private fun applyAudioProcessing() {
        rtcEngine?.let { engine ->
            // Enable AEC2 (new generation echo cancellation)
            engine.setParameters("{\"che.audio.enable_aec2\": true}")

            // Enable AGC (Automatic Gain Control)
            engine.setParameters("{\"che.audio.enable_agc\": true}")

            // Enable ANS (Automatic Noise Suppression)
            engine.setParameters("{\"che.audio.enable_ns\": true}")

            // Set AEC suppression level (0-3, higher = more aggressive)
            engine.setParameters("{\"che.audio.aec_suppression_level\": 3}")

            // Enable high-pass filter to remove low-frequency echo
            engine.setParameters("{\"che.audio.enable_hpf\": true}")

            Log.d(TAG, "Audio processing applied: AEC2, AGC, NS, HPF")
        }
    }

    private fun createEventHandler(): IRtcEngineEventHandler {
        return object : IRtcEngineEventHandler() {
            override fun onJoinChannelSuccess(channel: String?, uid: Int, elapsed: Int) {
                Log.d(TAG, "onJoinChannelSuccess: channel=$channel, uid=$uid")
                currentChannel = channel
                currentUid = uid

                // Ensure speakerphone is enabled after joining
                rtcEngine?.setEnableSpeakerphone(true)
                Log.d(TAG, "Speakerphone enabled: ${rtcEngine?.isSpeakerphoneEnabled()}")
            }

            override fun onLeaveChannel(stats: RtcStats?) {
                Log.d(TAG, "onLeaveChannel")
                currentChannel = null
                _connectionState.value = ConnectionState.DISCONNECTED
            }

            override fun onConnectionStateChanged(state: Int, reason: Int) {
                Log.d(TAG, "onConnectionStateChanged: state=$state, reason=$reason")
                _connectionState.value = when (state) {
                    Constants.CONNECTION_STATE_CONNECTED -> {
                        // Create data stream when connection is fully established
                        if (dataStreamId < 0 && currentChannel != null) {
                            Thread {
                                Thread.sleep(500) // Wait for connection to stabilize
                                val config = DataStreamConfig().apply {
                                    syncWithAudio = false
                                    ordered = false
                                }
                                val streamId = rtcEngine?.createDataStream(config) ?: -1
                                Log.d(TAG, "Data stream created after connection: $streamId")
                                dataStreamId = streamId
                            }.start()
                        }
                        ConnectionState.CONNECTED
                    }
                    Constants.CONNECTION_STATE_CONNECTING -> ConnectionState.CONNECTING
                    Constants.CONNECTION_STATE_RECONNECTING -> ConnectionState.RECONNECTING
                    Constants.CONNECTION_STATE_DISCONNECTED -> {
                        dataStreamId = -1
                        ConnectionState.DISCONNECTED
                    }
                    Constants.CONNECTION_STATE_FAILED -> {
                        dataStreamId = -1
                        ConnectionState.FAILED
                    }
                    else -> ConnectionState.DISCONNECTED
                }
            }

            override fun onAudioVolumeIndication(
                speakers: Array<AudioVolumeInfo>?,
                totalVolume: Int
            ) {
                if (totalVolume in 0..100) {
                    _audioVolume.value = totalVolume
                }
            }

            override fun onUserJoined(uid: Int, elapsed: Int) {
                Log.d(TAG, "onUserJoined: uid=$uid")
                _remoteUserJoined.tryEmit(uid)

                // Create data stream when remote user joins (connection is ready)
                // reliable: true, ordered: false
                if (dataStreamId < 0) {
                    dataStreamId = rtcEngine?.createDataStream(true, false) ?: -1
                    Log.d(TAG, "Data stream created in onUserJoined: $dataStreamId")
                }
            }

            override fun onUserOffline(uid: Int, reason: Int) {
                Log.d(TAG, "onUserOffline: uid=$uid, reason=$reason")
                _remoteUserLeft.tryEmit(uid)
            }

            override fun onStreamMessage(uid: Int, streamId: Int, data: ByteArray?) {
                data?.let {
                    val text = String(it)
                    Log.d(TAG, "onStreamMessageReceived: from uid=$uid, data=$text")

                    kotlinx.coroutines.runBlocking {
                        _dataMessageReceived.emit(RtcDataMessage(text, uid))
                    }
                }
            }

            override fun onStreamMessageError(uid: Int, streamId: Int, error: Int, missed: Int, cached: Int) {
                Log.e(TAG, "onStreamMessageError: uid=$uid, error=$error")
            }
        }
    }

    /**
     * Join an RTC channel.
     */
    fun joinChannel(token: String, channel: String, uid: Int): Result<Unit> {
        return try {
            _connectionState.value = ConnectionState.CONNECTING
            currentChannel = channel
            currentUid = uid

            // Use speakerphone for audio playback
            rtcEngine?.setEnableSpeakerphone(true)

            // Configure data stream before joining channel
            rtcEngine?.setParameters("{\"rtc.publish_custom_audio_track\": true}")

            rtcEngine?.joinChannel(token, channel, "", uid)

            Log.d(TAG, "Joined channel: $channel, Speakerphone: ${rtcEngine?.isSpeakerphoneEnabled()}")
            Result.success(Unit)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to join channel: ${e.message}")
            _connectionState.value = ConnectionState.FAILED
            Result.failure(e)
        }
    }

    /**
     * Enable local audio capture.
     */
    fun enableLocalAudio(enabled: Boolean) {
        rtcEngine?.enableLocalAudio(enabled)
    }

    /**
     * Mute/unmute local audio stream.
     */
    fun muteLocalAudio(muted: Boolean) {
        rtcEngine?.muteLocalAudioStream(muted)
        Log.d(TAG, "muteLocalAudio: $muted")
    }

    /**
     * Send a text message via data channel.
     * This is used for sending chat messages to the agent.
     */
    fun sendDataMessage(message: String): Result<Unit> {
        return try {
            val data = message.toByteArray(Charsets.UTF_8)

            // Check connection state before sending
            if (currentChannel == null) {
                Log.e(TAG, "Not in a channel")
                return Result.failure(Exception("Not ready to send"))
            }

            // Ensure data stream is created
            if (dataStreamId < 0) {
                Log.d(TAG, "Creating data stream before sending...")
                val config = DataStreamConfig().apply {
                    syncWithAudio = false
                    ordered = false
                }
                dataStreamId = rtcEngine?.createDataStream(config) ?: -1
                Log.d(TAG, "Data stream created: $dataStreamId")

                if (dataStreamId < 0) {
                    return Result.failure(Exception("Failed to create data stream"))
                }
            }

            Log.d(TAG, "Sending data message (streamId=$dataStreamId)")

            val errorCode = rtcEngine?.sendStreamMessage(dataStreamId, data)
            Log.d(TAG, "sendStreamMessage errorCode: $errorCode")
            // 0 means success
            if (errorCode == 0) {
                Result.success(Unit)
            } else {
                // Try recreating stream on error
                val config = DataStreamConfig().apply {
                    syncWithAudio = false
                    ordered = false
                }
                dataStreamId = rtcEngine?.createDataStream(config) ?: -1
                Log.d(TAG, "Retrying with new stream: $dataStreamId")
                val retryCode = rtcEngine?.sendStreamMessage(dataStreamId, data)
                if (retryCode == 0) {
                    Result.success(Unit)
                } else {
                    Result.failure(Exception("sendStreamMessage failed: $errorCode, retry: $retryCode"))
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to send data message: ${e.message}")
            Result.failure(e)
        }
    }

    /**
     * Send a chat message in the format expected by voice-assistant-with-memU.
     */
    fun sendChatMessage(
        text: String,
        role: String = "user",
        isFinal: Boolean = true,
        streamId: Int = 0
    ): Result<Unit> {
        val message = buildString {
            append("{")
            append("\"data_type\":\"transcribe\",")
            append("\"role\":\"$role\",")
            append("\"text\":\"$text\",")
            append("\"text_ts\":${System.currentTimeMillis()},")
            append("\"is_final\":$isFinal,")
            append("\"stream_id\":$streamId")
            append("}")
        }
        Log.d(TAG, "sendChatMessage: $message")
        return sendDataMessage(message)
    }

    /**
     * Get the stream ID for sending data messages.
     * Uses the current user's UID as the stream ID.
     */
    fun getStreamId(): Int = currentUid

    /**
     * Leave the current channel.
     */
    fun leaveChannel() {
        rtcEngine?.leaveChannel()
        currentChannel = null
        _connectionState.value = ConnectionState.DISCONNECTED
    }

    /**
     * Enable or disable the speakerphone.
     */
    fun setSpeakerphoneEnabled(enabled: Boolean) {
        rtcEngine?.setEnableSpeakerphone(enabled)
    }

    /**
     * Get the current channel name.
     */
    fun getCurrentChannel(): String? = currentChannel

    /**
     * Get the current user ID.
     */
    fun getCurrentUid(): Int = currentUid

    /**
     * Release all RTC resources.
     */
    fun release() {
        Log.d(TAG, "Releasing RTC resources")
        leaveChannel()
        RtcEngine.destroy()
        rtcEngine = null
    }
}
