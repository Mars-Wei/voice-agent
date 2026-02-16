# Android Voice Agent 改进计划

## 目标
参考 voice-assistant-with-memU example，完善 Android 端实现，实现完整的语音对话功能。

## 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                      Android 应用                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  UI Layer (Compose)                                      │   │
│  │  ├── WelcomeScreen     - 连接配置页面                      │   │
│  │  ├── ChatScreen        - 聊天主页面                        │   │
│  │  └── components        - 音频波形、消息卡片等               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ViewModel Layer                                         │   │
│  │  ├── WelcomeViewModel   - 连接配置逻辑                     │   │
│  │  └── ChatViewModel      - 聊天逻辑、状态管理                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Manager Layer                                           │   │
│  │  ├── AgoraRtcManager     - RTC 音频管理                   │   │
│  │  ├── AgoraRtmManager     - RTM 消息管理                   │   │
│  │  └── AudioManager        - 音频流处理                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Repository Layer                                        │   │
│  │  └── ChatRepository      - API 调用                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
         │                           │
         ▼                           ▼
┌─────────────────┐       ┌─────────────────────┐
│  Go Server API  │       │   Agora Cloud       │
│  /start, /stop  │       │   RTC/RTM           │
└─────────────────┘       └─────────────────────┘
```

## 需要改进的功能

### 1. 消息格式对齐
```
// 用户消息格式
{
  "data_type": "transcribe",
  "role": "user" | "assistant",
  "text": "消息内容",
  "text_ts": 1699999999999,
  "is_final": true,
  "stream_id": 123
}

// ASR 消息格式
{
  "data_type": "asr_result",
  "text": "识别文本",
  "final": true,
  "metadata": { "session_id": "100" }
}
```

### 2. Agora RTC 数据通道
- 使用 `sendStreamMessage` 发送消息
- 使用 `onStreamMessageReceived` 接收消息

### 3. 音频流处理
- 麦克风音频输入 -> Agora RTC
- Agora RTC -> 扬声器输出
- 音频波形可视化

### 4. 状态管理
- 连接状态 (CONNECTING, CONNECTED, DISCONNECTED)
- 消息状态 (SENDING, SENT, DELIVERED, ERROR)
- 音频状态 (LISTENING, SPEAKING, MUTED)

## 实现任务

### Phase 1: 基础架构完善
- [ ] 更新 API 客户端，支持更多配置
- [ ] 完善 AgoraRtcManager，添加数据通道支持
- [ ] 完善 AgoraRtmManager，添加消息处理

### Phase 2: 消息处理
- [ ] 添加消息解析器，支持 voice-assistant-with-memU 格式
- [ ] 添加消息队列管理
- [ ] 添加消息状态跟踪

### Phase 3: 音频功能
- [ ] 添加音频录制和播放
- [ ] 添加音频波形可视化
- [ ] 添加打断处理

### Phase 4: UI 优化
- [ ] 优化聊天界面
- [ ] 添加加载状态
- [ ] 添加错误提示

## 文件变更

### 新增文件
- `manager/AudioManager.kt` - 音频流管理
- `data/mapper/MessageMapper.kt` - 消息映射
- `domain/model/ChatMessage.kt` - 消息模型
- `presentation/viewmodel/ChatViewModel.kt` - 聊天逻辑

### 修改文件
- `manager/AgoraRtcManager.kt` - 添加数据通道
- `manager/AgoraRtmManager.kt` - 完善消息处理
- `data/repository/ChatRepository.kt` - 添加消息 API
- `presentation/ui/screens/chat/ChatScreen.kt` - 优化 UI

## 依赖更新
- Agora RTC SDK 4.x (已集成)
- Agora RTM SDK 2.x (已集成)
- Retrofit 2.9.0 (已集成)
- Kotlin Coroutines (已集成)
