"use client";

import React from "react";
import { Send } from "lucide-react";
import { cn } from "@/lib/utils";
import wallpaperImage from "@/assets/figma/wallpaper-56586a.png";
import avatarImage from "@/assets/figma/avatar-chat-602206.png";
import { useAppSelector, useAppDispatch } from "@/common";
import { addChatItem } from "@/store/reducers/global";
import {
    EMessageDataType,
    EMessageType,
    ERTMTextType,
    type IRTMTextItem,
    type IChatItem,
} from "@/types";
import MessageList from "@/components/Chat/MessageList";
import AudioWaveform from "@/components/Chat/AudioWaveform";
import { Button } from "@/components/ui/button";
import type { IMicrophoneAudioTrack } from "agora-rtc-sdk-ng";

interface ChatPageProps {
    className?: string;
}

export default function ChatPage({ className }: ChatPageProps) {
    const [inputValue, setInputValue] = React.useState("");
    const chatRef = React.useRef<HTMLDivElement>(null);
    const [audioTrack, setAudioTrack] = React.useState<IMicrophoneAudioTrack>();

    const rtmConnected = useAppSelector((state) => state.global.rtmConnected);
    const dispatch = useAppDispatch();
    const graphName = useAppSelector((state) => state.global.selectedGraphId);
    const agentConnected = useAppSelector((state) => state.global.agentConnected);
    const options = useAppSelector((state) => state.global.options);

    const disableInputMemo = React.useMemo(() => {
        return (
            !options.channel ||
            !options.userId ||
            !options.appId ||
            !options.token ||
            !rtmConnected ||
            !agentConnected
        );
    }, [
        options.channel,
        options.userId,
        options.appId,
        options.token,
        rtmConnected,
        agentConnected,
    ]);

    const onTextChanged = React.useCallback((text: IRTMTextItem) => {
        console.log("[ChatPage] RTM textChanged:", text);
        if (text.type == ERTMTextType.TRANSCRIBE) {
            const chatItem = {
                userId: options.userId,
                text: text.text,
                type: text.stream_id === "0" ? EMessageType.AGENT : EMessageType.USER,
                data_type: EMessageDataType.TEXT,
                isFinal: text.is_final,
                time: text.ts,
            };
            console.log("[ChatPage] Adding chat item from RTM:", chatItem);
            dispatch(addChatItem(chatItem));
        }
        if (text.type == ERTMTextType.INPUT_TEXT) {
            const chatItem = {
                userId: options.userId,
                text: text.text,
                type: EMessageType.USER,
                data_type: EMessageDataType.TEXT,
                isFinal: true,
                time: text.ts,
            };
            console.log("[ChatPage] Adding chat item from RTM INPUT_TEXT:", chatItem);
            dispatch(addChatItem(chatItem));
        }
    }, [dispatch, options.userId]);

    // Handle RTC textChanged events
    const onRtcTextChanged = React.useCallback((text: IChatItem) => {
        console.log("[ChatPage] RTC textChanged:", text);
        dispatch(addChatItem(text));
    }, [dispatch]);

    // Listen to RTC local tracks changes to get audio track
    React.useEffect(() => {
        if (typeof window === "undefined") return;

        const { rtcManager } = require("@/manager/rtc/rtc");

        const onLocalTracksChanged = (tracks: any) => {
            console.log("[ChatPage] Local tracks changed:", tracks);
            console.log("[ChatPage] Audio track:", tracks?.audioTrack ? "exists" : "missing");
            if (tracks?.audioTrack) {
                console.log("[ChatPage] Setting audio track");
                const track = tracks.audioTrack;

                // Ensure audio track is not muted
                if (track.muted) {
                    console.warn("[ChatPage] Audio track is muted, unmuting...");
                    track.setMuted(false);
                }

                // Monitor track state
                const mediaTrack = track.getMediaStreamTrack();
                if (mediaTrack.readyState === "ended") {
                    console.error("[ChatPage] Audio track has ended!");
                } else {
                    console.log("[ChatPage] Audio track state:", mediaTrack.readyState, "muted:", mediaTrack.muted);
                }

                setAudioTrack(track);
            }
        };

        // Get initial tracks
        console.log("[ChatPage] Initial check - rtcManager.localTracks:", rtcManager.localTracks);
        if (rtcManager.localTracks?.audioTrack) {
            console.log("[ChatPage] Found initial audio track");
            const track = rtcManager.localTracks.audioTrack;

            // Ensure audio track is not muted
            if (track.muted) {
                console.warn("[ChatPage] Initial audio track is muted, unmuting...");
                track.setMuted(false);
            }

            setAudioTrack(track);
        } else {
            console.log("[ChatPage] No initial audio track found");
        }

        rtcManager.on("localTracksChanged", onLocalTracksChanged);

        return () => {
            rtcManager.off("localTracksChanged", onLocalTracksChanged);
        };
    }, []);

    React.useEffect(() => {
        if (typeof window === "undefined") return;

        const { rtmManager } = require("@/manager/rtm");
        const { rtcManager } = require("@/manager/rtc/rtc");
        const { apiPing } = require("@/common/request");

        // Listen to RTM messages
        rtmManager.on("rtmMessage", onTextChanged);

        // Listen to RTC textChanged events
        rtcManager.on("textChanged", onRtcTextChanged);

        // Listen to RTC connection errors
        const onConnectionError = (error: any) => {
            console.error("[ChatPage] RTC connection error:", error);
            // You can add reconnection logic here if needed
        };
        rtcManager.on("connectionError", onConnectionError);

        // Monitor audio track state
        const checkAudioTrack = () => {
            if (audioTrack) {
                const track = audioTrack.getMediaStreamTrack();
                if (track.readyState === "ended") {
                    console.warn("[ChatPage] Audio track ended, attempting to recreate...");
                    // Track ended, might need to recreate
                } else if (track.muted) {
                    console.warn("[ChatPage] Audio track is muted");
                }
            }
        };

        // Health check: ping backend service periodically
        const healthCheck = async () => {
            if (options.channel && agentConnected) {
                try {
                    const result = await apiPing(options.channel);
                    console.log("[ChatPage] Health check ping result:", result);
                    if (result?.code !== 0) {
                        console.error("[ChatPage] Health check failed:", result);
                    }
                } catch (error) {
                    console.error("[ChatPage] Health check error:", error);
                }
            }
        };

        // Check audio track state periodically
        const audioCheckInterval = setInterval(checkAudioTrack, 5000);

        // Health check every 30 seconds
        const healthCheckInterval = setInterval(healthCheck, 30000);

        // Initial health check after 5 seconds
        setTimeout(healthCheck, 5000);

        return () => {
            rtmManager.off("rtmMessage", onTextChanged);
            rtcManager.off("textChanged", onRtcTextChanged);
            rtcManager.off("connectionError", onConnectionError);
            clearInterval(audioCheckInterval);
            clearInterval(healthCheckInterval);
        };
    }, [onTextChanged, onRtcTextChanged, audioTrack, options.channel, agentConnected]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setInputValue(e.target.value);
    };

    const handleInputSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        if (!inputValue || disableInputMemo || typeof window === "undefined") {
            return;
        }
        const { rtmManager } = require("@/manager/rtm");
        rtmManager.sendText(inputValue);
        setInputValue("");
    };

    return (
        <div
            className={cn("relative flex h-screen w-screen flex-col overflow-hidden", className)}
            style={{
                backgroundImage: `url(${wallpaperImage.src || wallpaperImage})`,
                backgroundSize: "cover",
                backgroundPosition: "center",
            }}
        >
            {/* Overlay with blur effect */}
            <div
                className="absolute inset-0"
                style={{
                    background: "rgba(0, 0, 0, 0.02)",
                    backdropFilter: "blur(172.2px)",
                }}
            />

            {/* Status bar */}
            <div className="absolute top-0 left-0 right-0 z-10 flex h-6 items-center justify-between px-6 text-xs text-black">
                <div className="flex items-center gap-2">
                    <span>周一 10月 10日</span>
                    <span>9:41</span>
                </div>
                <div className="flex items-center gap-1">
                    <div className="flex gap-0.5">
                        <div className="h-1 w-0.5 bg-black" />
                        <div className="h-1.5 w-0.5 bg-black" />
                        <div className="h-2 w-0.5 bg-black" />
                        <div className="h-2.5 w-0.5 bg-black" />
                    </div>
                    <div className="ml-1.5 flex items-center gap-1">
                        <div className="h-2 w-2 rounded-full bg-black" />
                        <span>100%</span>
                    </div>
                </div>
            </div>

            {/* Main content */}
            <div className="relative z-0 flex flex-1 flex-row overflow-hidden pt-6">
                {/* Avatar - Left side, larger */}
                <div className="relative flex-shrink-0 flex flex-col items-center px-12 pt-16">
                    <div
                        className="relative h-[500px] w-[500px] rounded-full"
                        style={{
                            background: "linear-gradient(180deg, #FFFFFF 0%, #D3BDD7 100%)",
                            boxShadow: "0 10px 40px rgba(0, 0, 0, 0.1)",
                        }}
                    >
                        <img
                            src={avatarImage.src || avatarImage}
                            alt="Avatar"
                            className="h-full w-full rounded-full object-cover"
                        />
                    </div>
                    {/* Audio waveform below avatar */}
                    <div className="mt-8 w-full max-w-[600px]">
                        <AudioWaveform audioTrack={audioTrack} />
                    </div>
                </div>

                {/* Messages area - Right side */}
                <div className="flex flex-1 flex-col overflow-hidden pr-12 pb-24 pt-16 min-h-0">
                    <div
                        className="flex-1 overflow-y-auto min-h-0"
                        ref={chatRef}
                    >
                        <MessageList className="pl-4" />
                    </div>
                </div>

                {/* Input area */}
                <div
                    className={cn("absolute bottom-0 left-0 right-0 z-10 border-t bg-white/30 p-4 backdrop-blur-sm", {
                        ["hidden"]: !graphName.includes("rtm"),
                    })}
                >
                    <form
                        onSubmit={handleInputSubmit}
                        className="mx-auto flex max-w-2xl items-center gap-2"
                    >
                        <input
                            type="text"
                            disabled={disableInputMemo}
                            placeholder="Type a message..."
                            value={inputValue}
                            onChange={handleInputChange}
                            className={cn(
                                "grow rounded-lg border bg-white/50 p-3 text-lg focus:outline-none focus:ring-2 focus:ring-purple-300",
                                {
                                    ["cursor-not-allowed opacity-50"]: disableInputMemo,
                                }
                            )}
                            style={{
                                fontFamily: "PingFang SC",
                                color: "#6A5B77",
                            }}
                        />
                        <Button
                            type="submit"
                            disabled={disableInputMemo || inputValue.length === 0}
                            size="icon"
                            className={cn("h-10 w-10 rounded-lg", {
                                ["opacity-50 cursor-not-allowed"]:
                                    disableInputMemo || inputValue.length === 0,
                            })}
                            style={{
                                background: "#886A86",
                            }}
                        >
                            <Send className="h-5 w-5 text-white" />
                        </Button>
                    </form>
                </div>
            </div>
        </div>
    );
}
