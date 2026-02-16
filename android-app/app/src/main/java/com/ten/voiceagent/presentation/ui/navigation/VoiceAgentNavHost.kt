package com.ten.voiceagent.presentation.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.ten.voiceagent.domain.model.AgentConfig
import com.ten.voiceagent.presentation.ui.screens.chat.ChatScreen
import com.ten.voiceagent.presentation.ui.screens.welcome.WelcomeScreen
import java.net.URLDecoder
import java.net.URLEncoder
import java.nio.charset.StandardCharsets

/**
 * Main navigation graph for the app.
 */
@Composable
fun VoiceAgentNavHost(
    navController: NavHostController,
    startDestination: String = Screen.Welcome.route,
    modifier: Modifier = Modifier
) {
    // Track config changes
    var pendingConfig by remember { mutableStateOf<AgentConfig?>(null) }

    NavHost(
        navController = navController,
        startDestination = startDestination,
        modifier = modifier
    ) {
        composable(Screen.Welcome.route) {
            WelcomeScreen(
                onNavigateToChat = { config ->
                    // Set pending config and navigate
                    pendingConfig = config
                    ConfigHolder.config = config
                    navController.navigate(Screen.Chat.routeWithArgs) {
                        popUpTo(Screen.Welcome.route) { inclusive = true }
                    }
                }
            )
        }

        composable(
            route = Screen.Chat.routeWithArgs,
            arguments = listOf(
                navArgument("channel") { type = NavType.StringType },
                navArgument("userId") { type = NavType.StringType },
                navArgument("graph") { type = NavType.StringType }
            )
        ) { backStackEntry ->
            val channel = backStackEntry.arguments?.getString("channel") ?: ""
            val userId = backStackEntry.arguments?.getString("userId")?.toIntOrNull() ?: 0
            val graph = backStackEntry.arguments?.getString("graph") ?: "voice_assistant"

            val config = remember(channel, userId, graph, pendingConfig) {
                pendingConfig ?: ConfigHolder.config ?: AgentConfig(
                    graphName = graph,
                    language = "zh-CN",
                    voiceType = "default",
                    channel = channel,
                    userId = userId
                )
            }

            // Clear pending config after use
            LaunchedEffect(config) {
                if (pendingConfig != null) {
                    pendingConfig = null
                }
            }

            ChatScreen(
                config = config,
                onNavigateToWelcome = {
                    ConfigHolder.config = null
                    pendingConfig = null
                    navController.navigate(Screen.Welcome.route) {
                        popUpTo(Screen.Chat.route) { inclusive = true }
                    }
                }
            )
        }
    }
}

/**
 * Static holder for passing config between screens.
 * This is a workaround since Navigation Compose doesn't support passing objects directly.
 */
object ConfigHolder {
    @Volatile
    var config: AgentConfig? = null
}

/**
 * Helper function to create route arguments for Chat screen.
 */
fun Screen.Companion.createChatRoute(
    channel: String,
    userId: Int,
    graph: String = "voice_assistant"
): String {
    val encodedChannel = URLEncoder.encode(channel, StandardCharsets.UTF_8.toString())
    val encodedUserId = URLEncoder.encode(userId.toString(), StandardCharsets.UTF_8.toString())
    val encodedGraph = URLEncoder.encode(graph, StandardCharsets.UTF_8.toString())
    return "chat/$encodedChannel/$encodedUserId/$encodedGraph"
}
