"use client";

import AgoraRTM, { type RTMClient, type RTMStreamChannel } from "agora-rtm";
import { apiGenAgoraData } from "@/common";
import { ERTMTextType, type IRTMTextItem } from "@/types";
import { AGEventEmitter } from "../events";

export interface IRtmEvents {
  rtmMessage: (text: any) => void; // TODO: update type
}

export type TRTMMessageEvent = {
  channelType: "STREAM" | "MESSAGE" | "USER";
  channelName: string;
  topicName?: string;
  messageType: "STRING" | "BINARY";
  customType?: string;
  publisher: string;
  message: string | Uint8Array;
  timestamp: number;
};

export class RtmManager extends AGEventEmitter<IRtmEvents> {
  private _joined: boolean;
  _client: RTMClient | null;
  channel: string = "";
  userId: number = 0;
  appId: string = "";
  token: string = "";

  constructor() {
    super();
    this._joined = false;
    this._client = null;
  }

  async init({
    channel,
    userId,
    appId,
    token,
  }: {
    channel: string;
    userId: number;
    appId: string;
    token: string;
  }) {
    if (this._joined) {
      return;
    }
    this.channel = channel;
    this.userId = userId;
    this.appId = appId;
    this.token = token;

    try {
      const rtm = new AgoraRTM.RTM(appId, String(userId), {
        logLevel: "debug", // TODO: use INFO
        // update config: https://doc.shengwang.cn/api-ref/rtm2/javascript/toc-configuration/configuration#rtmConfig
      });

      try {
        await rtm.login({ token });
        console.log("[RTM] Login successful");
      } catch (loginError: any) {
        console.error("[RTM] Login failed:", loginError);
        throw new Error(`RTM login failed: ${loginError?.code || loginError?.message || loginError}`);
      }

      try {
        // subscribe message channel(will be created automatically)
        const subscribeResult = await rtm.subscribe(channel, {
          withMessage: true,
          withPresence: true,
          beQuiet: false,
          withMetadata: true,
          withLock: true,
        });
        console.log(
          "[RTM] Subscribe Message Channel success!: ",
          subscribeResult
        );

        this._joined = true;
        this._client = rtm;

        // listen events
        this._listenRtmEvents();
      } catch (subscribeError: any) {
        console.error("[RTM] Failed to Create/Join Message Channel:", subscribeError);
        // Try to logout if login succeeded but subscribe failed
        try {
          await rtm.logout();
        } catch (logoutError) {
          console.error("[RTM] Logout error:", logoutError);
        }
        throw new Error(
          `RTM subscribe failed (Error Code: ${subscribeError?.code || 'unknown'}): ${subscribeError?.message || subscribeError}. ` +
          `This usually means RTM service is not enabled in your Agora project. ` +
          `You can continue using the app, but RTM text messaging features will be unavailable.`
        );
      }
    } catch (error: any) {
      console.error("[RTM] Initialization failed:", error);
      throw error;
    }
  }

  private _listenRtmEvents() {
    this._client!.addEventListener("message", this.handleRtmMessage.bind(this));
    // tmp add presence
    this._client!.addEventListener(
      "presence",
      this.handleRtmPresence.bind(this)
    );
    console.log("[RTM] Listen RTM events success!");
  }

  async handleRtmMessage(e: TRTMMessageEvent) {
    console.log("[RTM] [TRTMMessageEvent] RAW", JSON.stringify(e));
    const { message, messageType } = e;
    if (messageType === "STRING") {
      const msg: IRTMTextItem = JSON.parse(message as string);
      if (msg) {
        console.log("[RTM] Emitting rtmMessage event with msg:", msg);
        this.emit("rtmMessage", msg);
      }
    }
    if (messageType === "BINARY") {
      const decoder = new TextDecoder("utf-8");
      const decodedMessage = decoder.decode(message as Uint8Array);
      const msg: IRTMTextItem = JSON.parse(decodedMessage);
      this.emit("rtmMessage", msg);
    }
  }

  async handleRtmPresence(e: any) {
    console.log("[RTM] [TRTMPresenceEvent] RAW", JSON.stringify(e));
  }

  async sendText(text: string) {
    const msg: IRTMTextItem = {
      is_final: true,
      ts: Date.now(),
      text,
      type: ERTMTextType.INPUT_TEXT,
      stream_id: String(this.userId),
    };
    await this._client?.publish(this.channel, JSON.stringify(msg), {
      customType: "PainTxt",
    });
    this.emit("rtmMessage", msg);
  }

  async destroy() {
    // remove listener
    this._client?.removeEventListener(
      "message",
      this.handleRtmMessage.bind(this)
    );
    this._client?.removeEventListener(
      "presence",
      this.handleRtmPresence.bind(this)
    );
    // unsubscribe
    await this._client?.unsubscribe(this.channel);
    // logout
    await this._client?.logout();

    this._client = null;
    this._joined = false;
  }
}

export const rtmManager = new RtmManager();
