package com.ten.voiceagent.di;

import com.ten.voiceagent.data.api.ApiService;
import com.ten.voiceagent.data.repository.ChatRepository;
import dagger.internal.DaggerGenerated;
import dagger.internal.Factory;
import dagger.internal.Preconditions;
import dagger.internal.QualifierMetadata;
import dagger.internal.ScopeMetadata;
import javax.annotation.processing.Generated;
import javax.inject.Provider;

@ScopeMetadata("javax.inject.Singleton")
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
public final class AppModule_ProvideChatRepositoryFactory implements Factory<ChatRepository> {
  private final Provider<ApiService> apiServiceProvider;

  public AppModule_ProvideChatRepositoryFactory(Provider<ApiService> apiServiceProvider) {
    this.apiServiceProvider = apiServiceProvider;
  }

  @Override
  public ChatRepository get() {
    return provideChatRepository(apiServiceProvider.get());
  }

  public static AppModule_ProvideChatRepositoryFactory create(
      Provider<ApiService> apiServiceProvider) {
    return new AppModule_ProvideChatRepositoryFactory(apiServiceProvider);
  }

  public static ChatRepository provideChatRepository(ApiService apiService) {
    return Preconditions.checkNotNullFromProvides(AppModule.INSTANCE.provideChatRepository(apiService));
  }
}
