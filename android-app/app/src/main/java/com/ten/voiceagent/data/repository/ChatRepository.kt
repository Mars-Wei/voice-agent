package com.ten.voiceagent.data.repository

import android.util.Log
import com.google.gson.Gson
import com.google.gson.annotations.SerializedName
import com.ten.voiceagent.data.api.ApiService
import com.ten.voiceagent.data.api.dto.GenerateTokenRequest
import com.ten.voiceagent.data.api.dto.StartAgentRequest
import com.ten.voiceagent.data.api.dto.StopRequest
import com.ten.voiceagent.domain.model.AgoraTokenResponse
import com.ten.voiceagent.domain.model.AgentConfig
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Internal DTO matching server response format for token generation.
 */
data class AgoraTokenResponseDto(
    @SerializedName("appId")
    val appId: String,
    @SerializedName("token")
    val token: String,
    @SerializedName("channel_name")
    val channelName: String,
    @SerializedName("uid")
    val uid: Int
)

/**
 * Internal DTO for API response with Any data field.
 */
data class ApiResponseDto(
    @SerializedName("code")
    val code: String,
    @SerializedName("data")
    val data: Any?,
    @SerializedName("msg")
    val message: String?
)

/**
 * Repository for managing agent service operations.
 * Provides a clean API for the domain layer to interact with the backend services.
 * Matches web端 implementation.
 */
@Singleton
class ChatRepository @Inject constructor(
    private val apiService: ApiService
) {
    private val TAG = "ChatRepository"
    private val gson = Gson()

    /**
     * Generate a unique request ID.
     */
    private fun generateRequestId(): String = UUID.randomUUID().toString()

    /**
     * Start the voice agent with the given configuration.
     * Matches web端 apiStartService() implementation.
     */
    suspend fun startAgent(config: AgentConfig): Result<Unit> {
        return try {
            Log.d(TAG, "Starting agent: channel=${config.channel}, userId=${config.userId}")

            val request = StartAgentRequest(
                requestId = generateRequestId(),
                graphName = config.graphName,
                language = config.language,
                voiceType = config.voiceType,
                channelName = config.channel,
                userId = config.userId
            )

            val response = apiService.startAgent(request)
            val body = response.body()

            Log.d(TAG, "Start agent response: code=${body?.code}, msg=${body?.message}, data=${body?.data}")

            if (response.isSuccessful && body?.isSuccess == true) {
                Log.d(TAG, "Agent started successfully")
                Result.success(Unit)
            } else {
                Log.e(TAG, "Failed to start agent: ${body?.message}")
                Result.failure(Exception(body?.message ?: "Failed to start agent"))
            }
        } catch (e: Exception) {
            Log.e(TAG, "Exception starting agent: ${e.message}")
            Result.failure(e)
        }
    }

    /**
     * Stop the voice agent service.
     */
    suspend fun stopAgent(channelName: String): Result<Unit> {
        return try {
            val request = StopRequest(
                requestId = generateRequestId(),
                channelName = channelName
            )
            val response = apiService.stopAgent(request)
            val body = response.body()

            if (response.isSuccessful && body?.isSuccess == true) {
                Result.success(Unit)
            } else {
                Result.failure(Exception(body?.message ?: "Failed to stop agent"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Check if the agent service is running.
     */
    suspend fun ping(): Result<Unit> {
        return try {
            val response = apiService.ping()
            val body = response.body()

            if (response.isSuccessful && body?.isSuccess == true) {
                Result.success(Unit)
            } else {
                Result.failure(Exception(body?.message ?: "Agent not responding"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Generate Agora token for RTC/RTM connection.
     * Matches web端 apiGenAgoraData() implementation.
     */
    suspend fun getAgoraToken(channel: String, uid: Int): Result<AgoraTokenResponse> {
        return try {
            val request = GenerateTokenRequest(
                requestId = generateRequestId(),
                uid = uid,
                channelName = channel
            )

            val response = apiService.generateAgoraToken(request)
            val body = response.body()

            Log.d(TAG, "Token response: code=${body?.code}, msg=${body?.message}")

            if (response.isSuccessful && body?.isSuccess == true) {
                // Parse manually because server returns channel_name but Android expects channel
                val jsonData = gson.toJson(body.data)
                val dto = gson.fromJson(jsonData, AgoraTokenResponseDto::class.java)
                val tokenResponse = AgoraTokenResponse(
                    appId = dto.appId,
                    token = dto.token,
                    channelName = dto.channelName,
                    uid = dto.uid
                )
                Log.d(TAG, "Token generated: channel=${tokenResponse.channel}, uid=${tokenResponse.uid}")
                Result.success(tokenResponse)
            } else {
                Result.failure(Exception(body?.message ?: "Failed to generate token"))
            }
        } catch (e: Exception) {
            Log.e(TAG, "Exception generating token: ${e.message}")
            Result.failure(e)
        }
    }

    /**
     * Get list of available graph configurations.
     */
    suspend fun getGraphList(): Result<List<String>> {
        return try {
            val response = apiService.getGraphList()
            val body = response.body()

            if (response.isSuccessful && body?.isSuccess == true) {
                Result.success(body.data ?: emptyList())
            } else {
                Result.failure(Exception(body?.message ?: "Failed to get graph list"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
