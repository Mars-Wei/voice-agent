package com.ten.voiceagent.domain.model

/**
 * Configuration for connecting to the voice agent service.
 * Channel and userId are auto-generated.
 *
 * Based on web端 implementation:
 * - getRandomChannel() = "agora_" + random 6-char string
 * - getRandomUserId() = random number 100000-109999
 */
data class AgentConfig(
    val graphName: String = "voice_assistant",
    val language: String = "zh-CN",
    val voiceType: String = "default",
    val channel: String = generateChannel(),
    val userId: Int = generateUserId()
) {
    companion object {
        private const val CHANNEL_PREFIX = "agora_"
        private const val CHANNEL_RANDOM_LENGTH = 6

        /**
         * Generate a random channel name.
         * Matches web端 implementation: "agora_" + random 6-char alphanumeric string.
         */
        fun generateChannel(): String {
            val chars = "abcdefghijklmnopqrstuvwxyz0123456789"
            val random = (1..CHANNEL_RANDOM_LENGTH)
                .map { chars[java.security.SecureRandom().nextInt(chars.length)] }
                .joinToString("")
            return CHANNEL_PREFIX + random
        }

        /**
         * Generate a random user ID.
         * Matches web端 implementation: random number 100000-109999.
         */
        fun generateUserId(): Int {
            val random = java.security.SecureRandom()
            return random.nextInt(10000) + 100000
        }

        /**
         * Generate a new config with fresh random values.
         */
        fun createDefault(): AgentConfig {
            return AgentConfig(
                graphName = "voice_assistant",
                language = "zh-CN",
                voiceType = "default"
            )
        }
    }
}
