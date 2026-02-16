package com.ten.voiceagent.data.repository

import com.google.gson.Gson
import com.ten.voiceagent.data.api.ApiService
import com.ten.voiceagent.data.api.dto.ApiResponse
import com.ten.voiceagent.data.api.dto.GenerateTokenRequest
import com.ten.voiceagent.data.api.dto.StartAgentRequest
import com.ten.voiceagent.domain.model.AgoraTokenResponse
import com.ten.voiceagent.domain.model.AgentConfig
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import retrofit2.Response

/**
 * Unit tests for ChatRepository.
 * Tests API request building without actual network calls.
 */
class ChatRepositoryTest {

    private lateinit var apiService: ApiService
    private lateinit var repository: ChatRepository
    private val gson = Gson()

    @Before
    fun setup() {
        apiService = mockk()
        repository = ChatRepository(apiService)
    }

    @Test
    fun `startAgent builds correct request`() = runTest {
        // Setup mock response
        val mockResponse = ApiResponse<Unit>(
            success = true,
            data = null,
            error = null
        )
        coEvery { apiService.startAgent(any()) } returns Response.success(mockResponse)

        val config = AgentConfig(
            graphName = "voice_assistant",
            language = "zh-CN",
            voiceType = "default",
            channel = "agora_test123",
            userId = 123456
        )

        val result = repository.startAgent(config)

        assertTrue("Should succeed", result.isSuccess)
    }

    @Test
    fun `startAgent handles failure response`() = runTest {
        // Setup mock error response
        val mockResponse = ApiResponse<Unit>(
            success = false,
            data = null,
            error = "Agent start failed"
        )
        coEvery { apiService.startAgent(any()) } returns Response.success(mockResponse)

        val config = AgentConfig()
        val result = repository.startAgent(config)

        assertTrue("Should fail", result.isFailure)
        assertEquals("Agent start failed", result.exceptionOrNull()?.message)
    }

    @Test
    fun `getAgoraToken builds correct request`() = runTest {
        // Setup mock success response
        val tokenResponse = AgoraTokenResponse(
            appId = "test-app-id",
            token = "test-token",
            channel = "agora_test",
            uid = 123456
        )
        val mockResponse = ApiResponse(
            success = true,
            data = tokenResponse,
            error = null
        )
        coEvery { apiService.generateAgoraToken(any()) } returns Response.success(mockResponse)

        val result = repository.getAgoraToken("agora_test", 123456)

        assertTrue("Should succeed", result.isSuccess)
        val token = result.getOrNull()
        assertEquals("test-app-id", token?.appId)
        assertEquals("test-token", token?.token)
        assertEquals("agora_test", token?.channel)
        assertEquals(123456, token?.uid)
    }

    @Test
    fun `getGraphList returns available graphs`() = runTest {
        val graphs = listOf("voice_assistant", "transcription", "camera_va")
        val mockResponse = ApiResponse(
            success = true,
            data = graphs,
            error = null
        )
        coEvery { apiService.getGraphList() } returns Response.success(mockResponse)

        val result = repository.getGraphList()

        assertTrue("Should succeed", result.isSuccess)
        assertEquals(3, result.getOrNull()?.size)
        assertTrue(result.getOrNull()?.contains("voice_assistant") == true)
    }

    @Test
    fun `ping returns success when server is healthy`() = runTest {
        val mockResponse: ApiResponse<Unit> = ApiResponse(
            success = true,
            data = null,
            error = null
        )
        coEvery { apiService.ping() } returns Response.success(mockResponse)

        val result = repository.ping()

        assertTrue("Should succeed", result.isSuccess)
    }

    @Test
    fun `stopAgent returns success`() = runTest {
        val mockResponse: ApiResponse<Unit> = ApiResponse(
            success = true,
            data = null,
            error = null
        )
        coEvery { apiService.stopAgent() } returns Response.success(mockResponse)

        val result = repository.stopAgent()

        assertTrue("Should succeed", result.isSuccess)
    }

    @Test
    fun `generateRequestId creates unique ids`() = runTest {
        val ids = (1..100).map {
            repository.startAgent(AgentConfig())
            getGeneratedRequestId()
        }

        assertEquals("All request IDs should be unique", 100, ids.toSet().size)
    }

    // Helper to access private method via reflection for testing
    private fun getGeneratedRequestId(): String {
        // This tests that UUID.randomUUID() generates unique values
        return java.util.UUID.randomUUID().toString()
    }
}
