package com.ten.voiceagent.presentation.viewmodel;

import com.ten.voiceagent.data.repository.ChatRepository;
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
public final class WelcomeViewModel_Factory implements Factory<WelcomeViewModel> {
  private final Provider<ChatRepository> chatRepositoryProvider;

  public WelcomeViewModel_Factory(Provider<ChatRepository> chatRepositoryProvider) {
    this.chatRepositoryProvider = chatRepositoryProvider;
  }

  @Override
  public WelcomeViewModel get() {
    return newInstance(chatRepositoryProvider.get());
  }

  public static WelcomeViewModel_Factory create(Provider<ChatRepository> chatRepositoryProvider) {
    return new WelcomeViewModel_Factory(chatRepositoryProvider);
  }

  public static WelcomeViewModel newInstance(ChatRepository chatRepository) {
    return new WelcomeViewModel(chatRepository);
  }
}
