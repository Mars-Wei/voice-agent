package com.ten.voiceagent.data.api

import android.util.Log
import com.google.gson.Gson
import com.google.gson.GsonBuilder
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * Singleton object providing configured Retrofit instance.
 */
object ApiClient {
    private const val TAG = "ApiClient"

    /**
     * Base URL for the agent server.
     * For Android Emulator: Use 10.0.2.2 to access host's localhost
     * For Physical Device: Use actual IP address of the server
     */
    const val BASE_URL = "http://10.1.121.254:8080/"

    /**
     * Connection timeout in seconds.
     */
    private const val CONNECT_TIMEOUT = 30L

    /**
     * Read timeout in seconds.
     */
    private const val READ_TIMEOUT = 30L

    /**
     * Write timeout in seconds.
     */
    private const val WRITE_TIMEOUT = 30L

    private val gson: Gson = GsonBuilder()
        .setLenient()
        .create()

    private val loggingInterceptor: HttpLoggingInterceptor by lazy {
        HttpLoggingInterceptor { message ->
            Log.d(TAG, "OkHttp: $message")
        }.apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
    }

    private val okHttpClient: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .connectTimeout(CONNECT_TIMEOUT, TimeUnit.SECONDS)
            .readTimeout(READ_TIMEOUT, TimeUnit.SECONDS)
            .writeTimeout(WRITE_TIMEOUT, TimeUnit.SECONDS)
            .addInterceptor(loggingInterceptor)
            .addInterceptor { chain ->
                val original = chain.request()
                Log.d(TAG, "Request: ${original.method} ${original.url}")
                val request = original.newBuilder()
                    .header("Content-Type", "application/json")
                    .header("Accept", "application/json")
                    .method(original.method, original.body)
                    .build()
                chain.proceed(request)
            }
            .build()
    }

    private val retrofit: Retrofit by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    /**
     * Provides the configured ApiService instance.
     */
    val apiService: ApiService by lazy {
        retrofit.create(ApiService::class.java)
    }
}
