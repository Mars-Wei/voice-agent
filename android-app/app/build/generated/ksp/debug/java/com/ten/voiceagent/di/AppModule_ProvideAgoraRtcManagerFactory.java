package com.ten.voiceagent.di;

import android.content.Context;
import com.ten.voiceagent.manager.AgoraRtcManager;
import dagger.internal.DaggerGenerated;
import dagger.internal.Factory;
import dagger.internal.Preconditions;
import dagger.internal.QualifierMetadata;
import dagger.internal.ScopeMetadata;
import javax.annotation.processing.Generated;
import javax.inject.Provider;

@ScopeMetadata("javax.inject.Singleton")
@QualifierMetadata("dagger.hilt.android.qualifiers.ApplicationContext")
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
public final class AppModule_ProvideAgoraRtcManagerFactory implements Factory<AgoraRtcManager> {
  private final Provider<Context> contextProvider;

  public AppModule_ProvideAgoraRtcManagerFactory(Provider<Context> contextProvider) {
    this.contextProvider = contextProvider;
  }

  @Override
  public AgoraRtcManager get() {
    return provideAgoraRtcManager(contextProvider.get());
  }

  public static AppModule_ProvideAgoraRtcManagerFactory create(Provider<Context> contextProvider) {
    return new AppModule_ProvideAgoraRtcManagerFactory(contextProvider);
  }

  public static AgoraRtcManager provideAgoraRtcManager(Context context) {
    return Preconditions.checkNotNullFromProvides(AppModule.INSTANCE.provideAgoraRtcManager(context));
  }
}
