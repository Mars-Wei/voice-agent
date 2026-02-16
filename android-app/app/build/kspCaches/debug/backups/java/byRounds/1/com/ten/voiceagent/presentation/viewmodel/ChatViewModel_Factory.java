package com.ten.voiceagent.presentation.viewmodel;

import com.ten.voiceagent.data.repository.ChatRepository;
import com.ten.voiceagent.manager.AgoraRtcManager;
import dagger.internal.DaggerGenerated;
import dagger.internal.Factory;
import dagger.internal.QualifierMetadata;
import dagger.internal.ScopeMetadata;
import javax.annotation.processing.Generated;
import javax.inject.Provider;

@ScopeMetadata
@QualifierMetadata
@DaggerGenerated
@Generated(
    value = "dagger.internal.codegen.ComponentProcessor",
    comments = "https://dagger.dev"
)
@SuppressWarnings({
    "unchecked",
    "rawtypes",
    "KotlinInternal",
    "KotlinInternalInJava"
})
public final class ChatViewModel_Factory implements Factory<ChatViewModel> {
  private final Provider<ChatRepository> chatRepositoryProvider;

  private final Provider<AgoraRtcManager> rtcManagerProvider;

  public ChatViewModel_Factory(Provider<ChatRepository> chatRepositoryProvider,
      Provider<AgoraRtcManager> rtcManagerProvider) {
    this.chatRepositoryProvider = chatRepositoryProvider;
    this.rtcManagerProvider = rtcManagerProvider;
  }

  @Override
  public ChatViewModel get() {
    return newInstance(chatRepositoryProvider.get(), rtcManagerProvider.get());
  }

  public static ChatViewModel_Factory create(Provider<ChatRepository> chatRepositoryProvider,
      Provider<AgoraRtcManager> rtcManagerProvider) {
    return new ChatViewModel_Factory(chatRepositoryProvider, rtcManagerProvider);
  }

  public static ChatViewModel newInstance(ChatRepository chatRepository,
      AgoraRtcManager rtcManager) {
    return new ChatViewModel(chatRepository, rtcManager);
  }
}
