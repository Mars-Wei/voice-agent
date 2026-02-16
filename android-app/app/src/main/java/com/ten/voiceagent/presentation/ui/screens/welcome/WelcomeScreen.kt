package com.ten.voiceagent.presentation.ui.screens.welcome

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.ten.voiceagent.domain.model.AgentConfig
import com.ten.voiceagent.presentation.ui.navigation.ConfigHolder
import com.ten.voiceagent.presentation.ui.theme.Primary
import com.ten.voiceagent.presentation.viewmodel.WelcomeViewModel

/**
 * Welcome screen matching web端的 implementation.
 * User only needs to tap the connect button - channel and userId are auto-generated.
 */
@Composable
fun WelcomeScreen(
    onNavigateToChat: (AgentConfig) -> Unit,
    viewModel: WelcomeViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    // Navigate when config is ready
    LaunchedEffect(uiState.config) {
        uiState.config?.let { config ->
            ConfigHolder.config = config
            onNavigateToChat(config)
        }
    }

    Scaffold { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .background(
                    Brush.verticalGradient(
                        colors = listOf(
                            Color(0xFFFFF8F0),
                            Color(0xFFFFFFFF)
                        )
                    )
                )
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.SpaceBetween
            ) {
                Spacer(modifier = Modifier.height(48.dp))

                // Avatar Section
                AvatarSection()

                Spacer(modifier = Modifier.height(32.dp))

                // Greeting Text
                GreetingSection()

                Spacer(modifier = Modifier.weight(1f))

                // Feature Buttons
                FeatureSection()

                Spacer(modifier = Modifier.height(48.dp))

                // Connect Button - Simple Clickable
                SimpleConnectButton(
                    isLoading = uiState.isLoading,
                    onClick = {
                        viewModel.connect()
                    }
                )

                // Error Message
                uiState.error?.let { error ->
                    Spacer(modifier = Modifier.height(16.dp))
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.errorContainer
                        ),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(
                            text = error,
                            color = MaterialTheme.colorScheme.onErrorContainer,
                            modifier = Modifier.padding(16.dp),
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                }

                Spacer(modifier = Modifier.height(32.dp))
            }
        }
    }
}

@Composable
private fun SimpleConnectButton(
    isLoading: Boolean,
    onClick: () -> Unit
) {
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val scale by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = 1.08f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scale"
    )

    Column(
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Outer pulsing ring
        Box(
            modifier = Modifier
                .size((80 * scale).dp)
                .clip(CircleShape)
                .background(Color(0xFFFFC267).copy(alpha = 0.3f))
                .clickable(enabled = !isLoading) { onClick() },
            contentAlignment = Alignment.Center
        ) {
            // Button
            Box(
                modifier = Modifier
                    .size(72.dp)
                    .clip(CircleShape)
                    .background(Color(0xFFFBAA31)),
                contentAlignment = Alignment.Center
            ) {
                if (isLoading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(32.dp),
                        color = Color.White,
                        strokeWidth = 3.dp
                    )
                } else {
                    // Triangle icon
                    Canvas(modifier = Modifier.size(32.dp)) {
                        val path = Path().apply {
                            moveTo(size.width * 0.25f, size.height * 0.2f)
                            lineTo(size.width * 0.75f, size.height * 0.5f)
                            lineTo(size.width * 0.25f, size.height * 0.8f)
                            close()
                        }
                        drawPath(path, Color.White)
                    }
                }
            }
        }

        if (!isLoading) {
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = "点击连接",
                style = MaterialTheme.typography.bodySmall,
                color = Color(0xFF9E9E9E)
            )
        }
    }
}

@Composable
private fun AvatarSection() {
    Box(
        modifier = Modifier.size(200.dp),
        contentAlignment = Alignment.Center
    ) {
        // Background glow
        Box(
            modifier = Modifier
                .size(180.dp)
                .clip(CircleShape)
                .background(
                    Brush.radialGradient(
                        colors = listOf(
                            Primary.copy(alpha = 0.3f),
                            Primary.copy(alpha = 0.1f),
                            Color.Transparent
                        )
                    )
                )
        )

        // Avatar
        Box(
            modifier = Modifier
                .size(140.dp)
                .clip(CircleShape)
                .background(
                    Brush.linearGradient(
                        colors = listOf(Color(0xFFFFFFFF), Color(0xFFE8DEF8))
                    )
                ),
            contentAlignment = Alignment.Center
        ) {
            Canvas(modifier = Modifier.size(64.dp)) {
                val centerX = size.width / 2
                val centerY = size.height / 2
                drawCircle(
                    color = Primary,
                    radius = size.width * 0.25f,
                    center = Offset(centerX, centerY - size.height * 0.15f)
                )
                drawArc(
                    color = Primary,
                    startAngle = 0f,
                    sweepAngle = 180f,
                    useCenter = true,
                    topLeft = Offset(centerX - size.width * 0.3f, centerY + size.height * 0.1f),
                    size = Size(size.width * 0.6f, size.height * 0.4f)
                )
            }
        }
    }
}

@Composable
private fun GreetingSection() {
    Card(
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF8E7)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "HI,我是小搭子",
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF6A5B77)
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "时刻准备着，陪您聊天、解答问题\n还有更多技能等您探索",
                style = MaterialTheme.typography.bodyMedium,
                color = Color(0xFF8B7E96),
                textAlign = TextAlign.Center,
                lineHeight = 24.sp
            )
        }
    }
}

@Composable
private fun FeatureSection() {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceEvenly
    ) {
        FeatureItem("🎤", "语音聊天")
        FeatureItem("🎵", "卡拉OK")
        FeatureItem("💡", "智能问答")
    }
}

@Composable
private fun FeatureItem(icon: String, label: String) {
    Card(
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF8E7)),
        modifier = Modifier.width(100.dp)
    ) {
        Column(
            modifier = Modifier.padding(12.dp).fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(text = icon, style = MaterialTheme.typography.titleLarge)
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = label,
                style = MaterialTheme.typography.bodySmall,
                color = Color(0xFF6A5B77)
            )
        }
    }
}
