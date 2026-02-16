package com.ten.voiceagent.data.api

import com.google.gson.annotations.SerializedName
import com.ten.voiceagent.data.api.dto.GenerateTokenRequest
import com.ten.voiceagent.data.api.dto.StartAgentRequest
import com.ten.voiceagent.data.api.dto.StopRequest
import com.ten.voiceagent.domain.model.AgoraTokenResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

/**
 * Generic API response wrapper that handles various data types.
 */
data class ApiResponse<T>(
    @SerializedName("code")
    val code: String,
    @SerializedName("data")
    val data: T?,
    @SerializedName("msg")
    val message: String?
) {
    val isSuccess: Boolean
        get() = code == "0" || code == "0".lowercase()
}

/**
 * Retrofit API interface for agent server communication.
 * Base URL should be configured to point to the agent server (e.g., http://localhost:8080).
 *
 * Endpoints match the web端 implementation.
 */
interface ApiService {

    /**
     * Start the voice agent service.
     * Endpoint: POST /start
     */
    @POST("start")
    suspend fun startAgent(@Body request: StartAgentRequest): Response<ApiResponse<String>>

    /**
     * Stop the voice agent service.
     * Endpoint: POST /stop
     */
    @POST("stop")
    suspend fun stopAgent(@Body request: StopRequest): Response<ApiResponse<String>>

    /**
     * Check if the agent service is running.
     * Endpoint: POST /ping
     */
    @POST("ping")
    suspend fun ping(): Response<ApiResponse<String>>

    /**
     * Generate Agora RTC/RTM token.
     * Endpoint: POST /token/generate
     * Matches web端 implementation.
     */
    @POST("token/generate")
    suspend fun generateAgoraToken(
        @Body request: GenerateTokenRequest
    ): Response<ApiResponse<AgoraTokenResponse>>

    /**
     * Get list of available graphs.
     * Endpoint: GET /graphs
     */
    @GET("graphs")
    suspend fun getGraphList(): Response<ApiResponse<List<String>>>
}
