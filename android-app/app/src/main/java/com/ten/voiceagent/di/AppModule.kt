package com.ten.voiceagent.di

import android.content.Context
import com.ten.voiceagent.data.api.ApiService
import com.ten.voiceagent.data.api.ApiClient
import com.ten.voiceagent.data.repository.ChatRepository
import com.ten.voiceagent.manager.AgoraRtcManager
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

/**
 * Hilt module providing application-wide dependencies.
 */
@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideApiService(): ApiService {
        return ApiClient.apiService
    }

    @Provides
    @Singleton
    fun provideChatRepository(apiService: ApiService): ChatRepository {
        return ChatRepository(apiService)
    }

    @Provides
    @Singleton
    fun provideAgoraRtcManager(@ApplicationContext context: Context): AgoraRtcManager {
        return AgoraRtcManager(context)
    }
}
