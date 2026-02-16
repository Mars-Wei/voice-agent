package com.ten.voiceagent.presentation.ui.navigation

/**
 * Navigation routes for the app.
 */
sealed class Screen(val route: String) {
    data object Welcome : Screen("welcome")
    data object Chat : Screen("chat/{channel}/{userId}/{graph}") {
        val routeWithArgs: String = "chat/{channel}/{userId}/{graph}"

        fun createRoute(channel: String, userId: Int, graph: String = "voice_assistant"): String {
            return "chat/$channel/$userId/$graph"
        }
    }

    companion object {
        /**
         * Create a route for the Chat screen with the given parameters.
         */
        fun createChatRoute(channel: String, userId: Int, graph: String = "voice_assistant"): String {
            return "chat/$channel/$userId/$graph"
        }
    }
}
