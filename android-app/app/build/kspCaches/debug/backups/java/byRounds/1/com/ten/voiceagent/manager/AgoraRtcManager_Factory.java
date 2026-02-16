package com.ten.voiceagent.manager;

import android.content.Context;
import dagger.internal.DaggerGenerated;
import dagger.internal.Factory;
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
public final class AgoraRtcManager_Factory implements Factory<AgoraRtcManager> {
  private final Provider<Context> contextProvider;

  public AgoraRtcManager_Factory(Provider<Context> contextProvider) {
    this.contextProvider = contextProvider;
  }

  @Override
  public AgoraRtcManager get() {
    return newInstance(contextProvider.get());
  }

  public static AgoraRtcManager_Factory create(Provider<Context> contextProvider) {
    return new AgoraRtcManager_Factory(contextProvider);
  }

  public static AgoraRtcManager newInstance(Context context) {
    return new AgoraRtcManager(context);
  }
}
