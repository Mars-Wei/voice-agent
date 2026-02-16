package com.ten.voiceagent

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

/**
 * VoiceAgent Application class.
 * Annotated with @HiltAndroidApp to enable Hilt dependency injection.
 */
@HiltAndroidApp
class VoiceAgentApp : Application() {

    override fun onCreate() {
        super.onCreate()
        // Initialize any global configurations here
    }
}
