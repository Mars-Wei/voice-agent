package com.ten.voiceagent.domain.model

import org.junit.Assert.*
import org.junit.Test

/**
 * Unit tests for AgentConfig.
 * Tests the companion object methods for generating random values.
 */
class AgentConfigTest {

    @Test
    fun `generateChannel creates channel with correct prefix`() {
        val channel = AgentConfig.generateChannel()

        assertTrue("Channel should start with 'agora_'", channel.startsWith("agora_"))
    }

    @Test
    fun `generateChannel creates lowercase alphanumeric channel`() {
        val channel = AgentConfig.generateChannel()
        val randomPart = channel.substringAfter("agora_")

        assertTrue("Random part should only contain lowercase letters and digits",
            randomPart.all { it in 'a'..'z' || it in '0'..'9' })
    }

    @Test
    fun `generateChannel generates unique channels`() {
        val channels = (1..50).map { AgentConfig.generateChannel() }
        val uniqueChannels = channels.toSet()

        assertEquals("All 50 channels should be unique", 50, uniqueChannels.size)
    }

    @Test
    fun `generateUserId creates id in correct range`() {
        val userId = AgentConfig.generateUserId()

        assertTrue("UserId $userId should be >= 100000", userId >= 100000)
        assertTrue("UserId $userId should be <= 109999", userId <= 109999)
    }

    @Test
    fun `generateUserId generates mostly unique ids`() {
        val userIds = (1..50).map { AgentConfig.generateUserId() }
        val uniqueIds = userIds.toSet()

        // With 10000 possible values and 50 samples, we expect mostly unique IDs
        assertTrue("Should generate mostly unique IDs", uniqueIds.size > 40)
    }

    @Test
    fun `createDefault creates valid config`() {
        val config = AgentConfig.createDefault()

        assertEquals("voice_assistant", config.graphName)
        assertEquals("zh-CN", config.language)
        assertEquals("default", config.voiceType)
        assertTrue("Channel should start with agora_", config.channel.startsWith("agora_"))
        assertTrue("UserId should be in range", config.userId >= 100000)
    }

    @Test
    fun `default channel and userId are valid`() {
        val config = AgentConfig()

        assertTrue("Default channel should be valid", config.channel.startsWith("agora_"))
        assertTrue("Default userId should be >= 100000", config.userId >= 100000)
    }

    @Test
    fun `custom values are preserved`() {
        val config = AgentConfig(
            graphName = "custom_graph",
            language = "en-US",
            voiceType = "male",
            channel = "my_special_channel",
            userId = 999999
        )

        assertEquals("custom_graph", config.graphName)
        assertEquals("en-US", config.language)
        assertEquals("male", config.voiceType)
        assertEquals("my_special_channel", config.channel)
        assertEquals(999999, config.userId)
    }
}
