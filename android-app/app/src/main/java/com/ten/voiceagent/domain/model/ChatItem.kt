package com.ten.voiceagent.domain.model

/**
 * Represents a chat message in the conversation.
 */
data class ChatItem(
    val id: String,
    val streamId: Int = 0,
    val text: String,
    val isUser: Boolean,
    val timestamp: Long = System.currentTimeMillis(),
    val audioUrl: String? = null,
    val status: MessageStatus = MessageStatus.Sent
)
