package com.ten.voiceagent.domain.model

/**
 * Message delivery status.
 */
enum class MessageStatus {
    Sending,
    Sent,
    Delivered,
    Error
}

/**
 * Connection state for Agora services.
 */
enum class ConnectionState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
    RECONNECTING,
    FAILED
}
