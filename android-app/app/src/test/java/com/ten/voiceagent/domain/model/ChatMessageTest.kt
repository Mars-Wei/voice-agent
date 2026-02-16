package com.ten.voiceagent.domain.model

import org.junit.Assert.*
import org.junit.Test

/**
 * Unit tests for ChatMessage.
 */
class ChatMessageTest {

    @Test
    fun `fromJson parses user transcribe message correctly`() {
        val json = """{"data_type":"transcribe","role":"user","text":"Hello","text_ts":1699999999999,"is_final":true,"stream_id":123}"""

        val message = ChatMessage.fromJson(json)

        assertNotNull(message)
        assertEquals(MessageDataType.TRANSCRIBE, message?.dataType)
        assertEquals(MessageRole.USER, message?.role)
        assertEquals("Hello", message?.text)
        assertEquals(true, message?.isFinal)
        assertEquals(123, message?.streamId)
    }

    @Test
    fun `fromJson parses assistant message correctly`() {
        val json = """{"data_type":"transcribe","role":"assistant","text":"Hi there!","is_final":true,"stream_id":456}"""

        val message = ChatMessage.fromJson(json)

        assertNotNull(message)
        assertEquals(MessageRole.ASSISTANT, message?.role)
        assertEquals("Hi there!", message?.text)
    }

    @Test
    fun `fromJson parses asr result correctly`() {
        val json = """{"data_type":"asr_result","role":"user","text":"Speech text","is_final":true}"""

        val message = ChatMessage.fromJson(json)

        assertNotNull(message)
        assertEquals(MessageDataType.ASR_RESULT, message?.dataType)
    }

    @Test
    fun `fromJson parses raw message with reasoning correctly`() {
        val json = """{"data_type":"raw","role":"assistant","text":"reasoning content","is_final":false,"reasoning":true}"""

        val message = ChatMessage.fromJson(json)

        assertNotNull(message)
        assertEquals(MessageDataType.RAW, message?.dataType)
        assertEquals(true, message?.isReasoning)
    }

    @Test
    fun `fromJson handles missing optional fields`() {
        val json = """{"text":"Simple text"}"""

        val message = ChatMessage.fromJson(json)

        assertNotNull(message)
        assertEquals("Simple text", message?.text)
        assertEquals(MessageDataType.TRANSCRIBE, message?.dataType) // default
        assertEquals(MessageRole.USER, message?.role) // default
        assertEquals(true, message?.isFinal) // default
    }

    @Test
    fun `fromJson returns null for invalid json`() {
        val json = """{invalid json}"""

        val message = ChatMessage.fromJson(json)

        assertNull(message)
    }

    @Test
    fun `toJson generates correct format`() {
        val message = ChatMessage(
            dataType = MessageDataType.TRANSCRIBE,
            role = MessageRole.USER,
            text = "Test message",
            isFinal = true,
            streamId = 789
        )

        val json = message.toJson()

        assertTrue(json.contains("\"data_type\":\"transcribe\""))
        assertTrue(json.contains("\"role\":\"user\""))
        assertTrue(json.contains("\"text\":\"Test message\""))
        assertTrue(json.contains("\"is_final\":true"))
        assertTrue(json.contains("\"stream_id\":789"))
    }

    @Test
    fun `toJson escapes quotes in text`() {
        val message = ChatMessage(
            role = MessageRole.USER,
            text = "Hello \"World\"",
            isFinal = true
        )

        val json = message.toJson()

        assertTrue(json.contains("Hello \\\"World\\\""))
    }

    @Test
    fun `toJson includes reasoning flag when true`() {
        val message = ChatMessage(
            role = MessageRole.ASSISTANT,
            text = "Thinking...",
            isFinal = false,
            isReasoning = true
        )

        val json = message.toJson()

        assertTrue(json.contains("\"reasoning\":true"))
    }
}
