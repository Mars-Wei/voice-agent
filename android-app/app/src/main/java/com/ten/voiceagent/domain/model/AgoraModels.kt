package com.ten.voiceagent.domain.model

import com.google.gson.annotations.SerializedName

/**
 * Response from Agora token generation API.
 */
data class AgoraTokenResponse(
    @SerializedName("appId")
    val appId: String,
    @SerializedName("token")
    val token: String,
    @SerializedName("channel_name")
    val channelName: String,
    @SerializedName("uid")
    val uid: Int
) {
    // For compatibility, expose channel as well
    val channel: String get() = channelName
}
