package com.ten.voiceagent.di;

import com.ten.voiceagent.data.api.ApiService;
import dagger.internal.DaggerGenerated;
import dagger.internal.Factory;
import dagger.internal.Preconditions;
import dagger.internal.QualifierMetadata;
import dagger.internal.ScopeMetadata;
import javax.annotation.processing.Generated;

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
public final class AppModule_ProvideApiServiceFactory implements Factory<ApiService> {
  @Override
  public ApiService get() {
    return provideApiService();
  }

  public static AppModule_ProvideApiServiceFactory create() {
    return InstanceHolder.INSTANCE;
  }

  public static ApiService provideApiService() {
    return Preconditions.checkNotNullFromProvides(AppModule.INSTANCE.provideApiService());
  }

  private static final class InstanceHolder {
    private static final AppModule_ProvideApiServiceFactory INSTANCE = new AppModule_ProvideApiServiceFactory();
  }
}
