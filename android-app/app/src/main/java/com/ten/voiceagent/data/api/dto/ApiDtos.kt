package com.ten.voiceagent.data.api.dto

import com.google.gson.annotations.SerializedName

/**
 * Request body for starting an agent.
 * Matches web端 implementation with request_id for tracking.
 */
data class StartAgentRequest(
    @SerializedName("request_id")
    val requestId: String,
    @SerializedName("graph_name")
    val graphName: String,
    @SerializedName("language")
    val language: String,
    @SerializedName("voice_type")
    val voiceType: String,
    @SerializedName("channel_name")
    val channelName: String,
    @SerializedName("user_uid")
    val userId: Int
)

/**
 * Request body for generating Agora token.
 * Matches web端 implementation.
 */
data class GenerateTokenRequest(
    @SerializedName("request_id")
    val requestId: String,
    @SerializedName("uid")
    val uid: Int,
    @SerializedName("channel_name")
    val channelName: String
)

/**
 * Generic API response wrapper.
 * Matches web端 format: {"code": "0", "data": {...}, "msg": "success"}
 * Note: data can be any type (object, array, number, or null)
 */
data class ApiResponse<T>(
    @SerializedName("code")
    val code: String,
    @SerializedName("data")
    val data: T?,
    @SerializedName("msg")
    val message: String?
) {
    /**
     * Check if the response is successful.
     * Code "0" means success.
     */
    val isSuccess: Boolean
        get() = code == "0" || code == "0".lowercase()

    /**
     * Get error message if any.
     */
    val errorMessage: String?
        get() = if (isSuccess) null else message
}

/**
 * Graph configuration from the server.
 */
data class GraphConfig(
    @SerializedName("id")
    val id: String,
    @SerializedName("name")
    val name: String,
    @SerializedName("description")
    val description: String?
)

/**
 * Request body for stopping an agent.
 */
data class StopRequest(
    @SerializedName("request_id")
    val requestId: String,
    @SerializedName("channel_name")
    val channelName: String
)

/**
 * Request body for ping to keep agent alive.
 */
data class PingRequest(
    @SerializedName("request_id")
    val requestId: String,
    @SerializedName("channel_name")
    val channelName: String
)
