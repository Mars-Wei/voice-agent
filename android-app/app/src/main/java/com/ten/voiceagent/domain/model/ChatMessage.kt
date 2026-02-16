package com.ten.voiceagent.domain.model

import android.util.Base64
import com.google.gson.Gson
import com.google.gson.annotations.SerializedName

/**
 * Message data type for voice-assistant-with-memU.
 */
enum class MessageDataType {
    TRANSCRIBE,      // 转录消息
    ASR_RESULT,      // ASR 识别结果
    RAW              // 原始消息
}

/**
 * Message role in the conversation.
 */
enum class MessageRole {
    USER,
    ASSISTANT,
    SYSTEM
}

/**
 * Chat message that matches voice-assistant-with-memU format.
 * {
 *   "data_type": "transcribe",
 *   "role": "user" | "assistant",
 *   "text": "消息内容",
 *   "text_ts": 1699999999999,
 *   "is_final": true,
 *   "stream_id": 123
 * }
 */
data class ChatMessage(
    val id: String = java.util.UUID.randomUUID().toString(),
    val dataType: MessageDataType = MessageDataType.TRANSCRIBE,
    val role: MessageRole,
    val text: String,
    val timestamp: Long = System.currentTimeMillis(),
    val textTimestamp: Long = System.currentTimeMillis(),
    val isFinal: Boolean = true,
    val streamId: Int = 0,
    val status: MessageStatus = MessageStatus.Delivered,
    val isReasoning: Boolean = false
) {
    /**
     * Convert to JSON string for sending via RTC/RTM.
     */
    fun toJson(): String {
        return buildString {
            append("{")
            append("\"data_type\":\"${dataType.name.lowercase()}\",")
            append("\"role\":\"${role.name.lowercase()}\",")
            append("\"text\":\"${text.replace("\"", "\\\"")}\",")
            append("\"text_ts\":$textTimestamp,")
            append("\"is_final\":$isFinal,")
            append("\"stream_id\":$streamId")
            if (isReasoning) {
                append(",\"reasoning\":true")
            }
            append("}")
        }
    }

    companion object {
        private val gson = Gson()

        /**
         * Parse message from RTC data channel.
         * Format: "id|streamId|customParam|base64_json"
         * Or plain JSON string.
         */
        fun fromJson(data: String): ChatMessage? {
            return try {
                val jsonContent = if (data.contains("|")) {
                    // Parse format: id|streamId|customParam|base64_json
                    val parts = data.split("|")
                    if (parts.size >= 4) {
                        String(Base64.decode(parts[3], Base64.DEFAULT))
                    } else {
                        data
                    }
                } else {
                    data
                }

                val map = gson.fromJson(jsonContent, Map::class.java) as Map<String, Any>
                val dataTypeStr = map["data_type"] as? String ?: "transcribe"
                val roleStr = map["role"] as? String ?: "user"
                val text = map["text"] as? String ?: ""
                val isFinal = (map["is_final"] as? Boolean) ?: true
                val streamId = (map["stream_id"] as? Number)?.toInt() ?: 0
                val textTs = (map["text_ts"] as? Number)?.toLong() ?: System.currentTimeMillis()
                val isReasoning = (map["reasoning"] as? Boolean) ?: false

                ChatMessage(
                    dataType = when (dataTypeStr) {
                        "asr_result" -> MessageDataType.ASR_RESULT
                        "raw" -> MessageDataType.RAW
                        else -> MessageDataType.TRANSCRIBE
                    },
                    role = when (roleStr) {
                        "assistant" -> MessageRole.ASSISTANT
                        "system" -> MessageRole.SYSTEM
                        else -> MessageRole.USER
                    },
                    text = text,
                    isFinal = isFinal,
                    streamId = streamId,
                    textTimestamp = textTs,
                    isReasoning = isReasoning
                )
            } catch (e: Exception) {
                null
            }
        }
    }
}
