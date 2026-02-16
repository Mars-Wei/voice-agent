package com.ten.voiceagent.presentation.ui.screens.chat

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CallEnd
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.MicOff
import androidx.compose.material.icons.filled.RecordVoiceOver
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.Speaker
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.ten.voiceagent.domain.model.AgentConfig
import com.ten.voiceagent.domain.model.ChatItem
import com.ten.voiceagent.domain.model.ConnectionState
import com.ten.voiceagent.domain.model.MessageStatus
import com.ten.voiceagent.presentation.ui.theme.*
import com.ten.voiceagent.presentation.viewmodel.ChatViewModel
import kotlinx.coroutines.flow.collectLatest
import java.text.SimpleDateFormat
import java.util.*

/**
 * Main chat screen with voice agent.
 * Compatible with voice-assistant-with-memU message flow.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(
    config: AgentConfig? = null,
    onNavigateToWelcome: () -> Unit,
    viewModel: ChatViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    // Connect to agent when screen loads
    LaunchedEffect(config) {
        config?.let {
            viewModel.connect(it)
        }
    }

    // Handle navigation events
    LaunchedEffect(Unit) {
        viewModel.navigationEvent.collectLatest { event ->
            when (event) {
                is ChatViewModel.NavigationEvent.NavigateToWelcome -> onNavigateToWelcome()
            }
        }
    }

    // Show error snackbar
    LaunchedEffect(uiState.error) {
        uiState.error?.let { error ->
            snackbarHostState.showSnackbar(error)
            viewModel.clearError()
        }
    }

    Scaffold(
        topBar = {
            ChatTopBar(
                connectionState = uiState.connectionState,
                agentName = uiState.agentName,
                onDisconnect = viewModel::disconnect
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // Agent Status Section
            AgentStatusSection(
                isListening = uiState.isListening,
                isSpeaking = uiState.isSpeaking,
                isMicrophoneEnabled = uiState.isMicrophoneEnabled,
                audioVolume = uiState.audioVolume,
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(0.35f)
            )

            // Message List Section
            MessageListSection(
                messages = uiState.messages,
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(0.45f)
            )

            // Input Section
            ChatInputSection(
                text = uiState.inputText,
                onTextChange = viewModel::updateInputText,
                onSend = viewModel::sendMessage,
                onMicrophoneToggle = viewModel::toggleMicrophone,
                isMicrophoneEnabled = uiState.isMicrophoneEnabled,
                isConnected = uiState.isConnected,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ChatTopBar(
    connectionState: ConnectionState,
    agentName: String,
    onDisconnect: () -> Unit
) {
    TopAppBar(
        title = {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // Connection status indicator
                Box(
                    modifier = Modifier
                        .size(10.dp)
                        .clip(CircleShape)
                        .background(
                            when (connectionState) {
                                ConnectionState.CONNECTED -> StatusConnected
                                ConnectionState.CONNECTING, ConnectionState.RECONNECTING -> StatusConnecting
                                else -> StatusDisconnected
                            }
                        )
                )
                Text(
                    text = agentName,
                    style = MaterialTheme.typography.titleMedium
                )
            }
        },
        actions = {
            // Connection status text
            Text(
                text = when (connectionState) {
                    ConnectionState.CONNECTED -> "已连接"
                    ConnectionState.CONNECTING -> "连接中..."
                    ConnectionState.RECONNECTING -> "重连中..."
                    ConnectionState.FAILED -> "连接失败"
                    else -> "未连接"
                },
                style = MaterialTheme.typography.bodySmall,
                color = when (connectionState) {
                    ConnectionState.CONNECTED -> StatusConnected
                    ConnectionState.CONNECTING, ConnectionState.RECONNECTING -> StatusConnecting
                    else -> MaterialTheme.colorScheme.error
                },
                modifier = Modifier.padding(end = 8.dp)
            )
            IconButton(onClick = onDisconnect) {
                Icon(
                    imageVector = Icons.Default.CallEnd,
                    contentDescription = "Disconnect",
                    tint = MaterialTheme.colorScheme.error
                )
            }
        },
        colors = TopAppBarDefaults.topAppBarColors(
            containerColor = MaterialTheme.colorScheme.surface
        )
    )
}

@Composable
private fun AgentStatusSection(
    isListening: Boolean,
    isSpeaking: Boolean,
    isMicrophoneEnabled: Boolean,
    audioVolume: Int,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier,
        contentAlignment = Alignment.Center
    ) {
        when {
            isSpeaking -> {
                // Speaking state - show waveform
                AgentSpeakingVisualizer(
                    isActive = true,
                    modifier = Modifier.fillMaxSize()
                )
            }
            isListening -> {
                // Listening state - show microphone with volume
                AgentListeningVisualizer(
                    volume = audioVolume,
                    isActive = isMicrophoneEnabled,
                    modifier = Modifier.fillMaxSize()
                )
            }
            else -> {
                // Idle state
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Icon(
                        imageVector = if (isMicrophoneEnabled) Icons.Default.Mic else Icons.Default.MicOff,
                        contentDescription = null,
                        modifier = Modifier.size(64.dp),
                        tint = MaterialTheme.colorScheme.outline
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = if (isMicrophoneEnabled) "点击开始对话" else "麦克风已静音",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    }
}

@Composable
private fun AgentSpeakingVisualizer(
    isActive: Boolean,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "speaking")
    val phase by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 2f * Math.PI.toFloat(),
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "phase"
    )

    val colors = listOf(
        AgentSpeaking1,
        AgentSpeaking2,
        AgentSpeaking3,
        AgentSpeaking2,
        AgentSpeaking1
    )

    Canvas(modifier = modifier.padding(24.dp)) {
        val centerX = size.width / 2
        val centerY = size.height / 2
        val maxRadius = minOf(size.width, size.height) * 0.4f

        for (i in 0 until 5) {
            val radius = maxRadius * (0.4f + 0.12f * i)
            val alpha = (0.3f + 0.15f * i).coerceAtMost(1f)
            val wave = kotlin.math.sin(phase + i * 0.5f) * 0.2f + 0.8f

            drawCircle(
                color = colors[i].copy(alpha = alpha * wave),
                radius = radius,
                center = Offset(centerX, centerY),
                style = androidx.compose.ui.graphics.drawscope.Stroke(width = 4.dp.toPx())
            )
        }
    }
}

@Composable
private fun AgentListeningVisualizer(
    volume: Int,
    isActive: Boolean,
    modifier: Modifier = Modifier
) {
    val animatedVolume by animateIntAsState(
        targetValue = volume,
        animationSpec = tween(durationMillis = 50),
        label = "volume"
    )

    val infiniteTransition = rememberInfiniteTransition(label = "idle")
    val phase by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 2f * Math.PI.toFloat(),
        animationSpec = infiniteRepeatable(
            animation = tween(2000),
            repeatMode = RepeatMode.Restart
        ),
        label = "phase"
    )

    val barCount = 12
    val primaryColor = if (isActive) AgentListening else AgentListeningInactive

    Canvas(modifier = modifier.padding(16.dp)) {
        val barWidth = size.width / (barCount * 2.5f)
        val maxBarHeight = size.height * 0.6f
        val centerY = size.height / 2

        for (i in 0 until barCount) {
            val x = i * barWidth * 2 + barWidth / 2

            // Calculate wave effect for idle animation
            val waveHeight = kotlin.math.sin(phase + i * 0.4f) * 3 + 3
            val volumeHeight = (animatedVolume / 100f) * maxBarHeight * 0.4f
            val barHeight = (volumeHeight + waveHeight).coerceIn(barWidth, maxBarHeight)

            val color = primaryColor

            drawRoundRect(
                color = color,
                topLeft = Offset(x, centerY - barHeight / 2),
                size = Size(barWidth, barHeight),
                cornerRadius = androidx.compose.ui.geometry.CornerRadius(barWidth / 2)
            )
        }
    }
}

@Composable
private fun MessageListSection(
    messages: List<ChatItem>,
    modifier: Modifier = Modifier
) {
    val listState = rememberLazyListState()

    // Auto-scroll to bottom when new messages arrive
    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) {
            listState.animateScrollToItem(messages.size - 1)
        }
    }

    if (messages.isEmpty()) {
        Box(
            modifier = modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Icon(
                    imageVector = Icons.Default.RecordVoiceOver,
                    contentDescription = null,
                    modifier = Modifier.size(48.dp),
                    tint = MaterialTheme.colorScheme.outline
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "开始与 AI 助手对话",
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    } else {
        LazyColumn(
            state = listState,
            modifier = modifier,
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(messages, key = { it.id }) { message ->
                ChatMessageCard(message = message)
            }
        }
    }
}

@Composable
private fun ChatMessageCard(message: ChatItem) {
    val alignment = if (message.isUser) Alignment.End else Alignment.Start
    val backgroundColor = if (message.isUser) {
        MaterialTheme.colorScheme.primaryContainer
    } else {
        MaterialTheme.colorScheme.secondaryContainer
    }
    val shape = RoundedCornerShape(
        topStart = 16.dp,
        topEnd = 16.dp,
        bottomStart = if (message.isUser) 16.dp else 4.dp,
        bottomEnd = if (message.isUser) 4.dp else 16.dp
    )

    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = alignment
    ) {
        Card(
            shape = shape,
            colors = CardDefaults.cardColors(containerColor = backgroundColor),
            modifier = Modifier.widthIn(max = 280.dp)
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(
                    text = message.text,
                    style = MaterialTheme.typography.bodyMedium,
                    color = if (message.isUser) {
                        MaterialTheme.colorScheme.onPrimaryContainer
                    } else {
                        MaterialTheme.colorScheme.onSecondaryContainer
                    }
                )

                Spacer(modifier = Modifier.height(4.dp))

                Row(
                    modifier = Modifier.align(alignment),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    Text(
                        text = formatTimestamp(message.timestamp),
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )

                    if (message.isUser) {
                        MessageStatusIndicator(status = message.status)
                    }
                }
            }
        }
    }
}

@Composable
private fun MessageStatusIndicator(status: MessageStatus) {
    val color = when (status) {
        MessageStatus.Sending -> MaterialTheme.colorScheme.outline
        MessageStatus.Sent -> MaterialTheme.colorScheme.outline
        MessageStatus.Delivered -> StatusConnected
        MessageStatus.Error -> StatusError
    }

    Icon(
        imageVector = Icons.Default.VolumeUp,
        contentDescription = null,
        modifier = Modifier.size(12.dp),
        tint = color
    )
}

@Composable
private fun ChatInputSection(
    text: String,
    onTextChange: (String) -> Unit,
    onSend: () -> Unit,
    onMicrophoneToggle: () -> Unit,
    isMicrophoneEnabled: Boolean,
    isConnected: Boolean,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        tonalElevation = 2.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Microphone Toggle
            FilledIconButton(
                onClick = onMicrophoneToggle,
                enabled = isConnected,
                colors = IconButtonDefaults.filledIconButtonColors(
                    containerColor = if (isMicrophoneEnabled) {
                        MaterialTheme.colorScheme.primary
                    } else {
                        MaterialTheme.colorScheme.errorContainer
                    }
                )
            ) {
                Icon(
                    imageVector = if (isMicrophoneEnabled) Icons.Default.Mic else Icons.Default.MicOff,
                    contentDescription = if (isMicrophoneEnabled) "Mute" else "Unmute"
                )
            }

            // Text Input
            OutlinedTextField(
                value = text,
                onValueChange = onTextChange,
                placeholder = { Text("输入消息...") },
                singleLine = false,
                maxLines = 3,
                modifier = Modifier.weight(1f),
                enabled = isConnected
            )

            // Send Button
            FilledIconButton(
                onClick = onSend,
                enabled = isConnected && text.isNotBlank()
            ) {
                Icon(
                    imageVector = Icons.Default.Send,
                    contentDescription = "Send"
                )
            }
        }
    }
}

private fun formatTimestamp(timestamp: Long): String {
    val sdf = SimpleDateFormat("HH:mm", Locale.getDefault())
    return sdf.format(Date(timestamp))
}
