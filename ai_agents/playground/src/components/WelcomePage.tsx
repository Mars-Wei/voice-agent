"use client";

import React from "react";
import { cn } from "@/lib/utils";
import wallpaperImage from "@/assets/figma/wallpaper-56586a.png";
import avatarImage from "@/assets/figma/avatar-602206.png";

interface WelcomePageProps {
    onConnect: () => void;
    isConnecting?: boolean;
}

export default function WelcomePage({
    onConnect,
    isConnecting = false,
}: WelcomePageProps) {
    return (
        <div
            className="relative flex h-screen w-screen items-center justify-center overflow-hidden"
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

            {/* Status bar (simplified) */}
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
            <div className="relative z-0 flex flex-col items-center">
                {/* Avatar and greeting card */}
                <div className="mb-12 flex flex-col items-center">
                    {/* Avatar image */}
                    <div className="relative mb-8">
                        <div
                            className="relative h-64 w-64 rounded-full"
                            style={{
                                background: "linear-gradient(180deg, #FFFFFF 0%, #D3BDD7 100%)",
                            }}
                        >
                            <img
                                src={avatarImage.src || avatarImage}
                                alt="Avatar"
                                className="h-full w-full rounded-full object-cover"
                            />
                        </div>
                    </div>

                    {/* Greeting card */}
                    <div
                        className="rounded-2xl px-8 py-4 text-center"
                        style={{
                            background: "rgba(255, 255, 255, 0.77)",
                            backdropFilter: "blur(95.2px)",
                        }}
                    >
                        <p
                            className="text-xl leading-relaxed"
                            style={{
                                fontFamily: "PingFang SC",
                                fontWeight: 500,
                                color: "#6A5B77",
                            }}
                        >
                            HI,我是的智慧搭子，时刻准备着
                            <br />
                            陪您唱歌，陪您解闷，还有很多其他技能等您解锁
                        </p>
                    </div>
                </div>

                {/* Feature buttons */}
                <div className="mb-12 flex gap-4">
                    <div
                        className="flex items-center gap-2 rounded-xl px-3.5 py-2.5"
                        style={{
                            background: "rgba(255, 255, 255, 0.3)",
                        }}
                    >
                        <div className="h-6 w-6">
                            <svg
                                viewBox="0 0 26 26"
                                fill="none"
                                xmlns="http://www.w3.org/2000/svg"
                            >
                                <rect x="5" y="3" width="16" height="20" rx="2" fill="#6A5B77" />
                                <rect x="10" y="3" width="10" height="2" fill="white" />
                                <rect x="7" y="3" width="7" height="2" fill="white" />
                            </svg>
                        </div>
                        <span
                            className="text-base"
                            style={{
                                fontFamily: "PingFang SC",
                                fontWeight: 500,
                                color: "#6A5B77",
                            }}
                        >
                            卡拉OK
                        </span>
                    </div>

                    <div
                        className="flex items-center gap-2 rounded-xl px-3.5 py-2.5"
                        style={{
                            background: "rgba(255, 255, 255, 0.3)",
                        }}
                    >
                        <div className="h-6 w-6">
                            <svg
                                viewBox="0 0 26 26"
                                fill="none"
                                xmlns="http://www.w3.org/2000/svg"
                            >
                                <circle cx="13" cy="13" r="10" fill="#6A5B77" />
                            </svg>
                        </div>
                        <span
                            className="text-base"
                            style={{
                                fontFamily: "PingFang SC",
                                fontWeight: 500,
                                color: "#6A5B77",
                            }}
                        >
                            视频通话
                        </span>
                    </div>

                    <div
                        className="flex items-center gap-2 rounded-xl px-3.5 py-2.5"
                        style={{
                            background: "rgba(255, 255, 255, 0.3)",
                        }}
                    >
                        <div className="h-6 w-6">
                            <svg
                                viewBox="0 0 26 26"
                                fill="none"
                                xmlns="http://www.w3.org/2000/svg"
                            >
                                <path
                                    d="M13 2L15.5 9.5L23 12L15.5 14.5L13 22L10.5 14.5L3 12L10.5 9.5L13 2Z"
                                    fill="#6A5B77"
                                />
                            </svg>
                        </div>
                        <span
                            className="text-base"
                            style={{
                                fontFamily: "PingFang SC",
                                fontWeight: 500,
                                color: "#6A5B77",
                            }}
                        >
                            服药提醒
                        </span>
                    </div>
                </div>

                {/* Connect button */}
                <button
                    onClick={onConnect}
                    disabled={isConnecting}
                    className={cn(
                        "relative h-12 w-12 rounded-full transition-all",
                        {
                            ["opacity-50 cursor-not-allowed"]: isConnecting,
                            ["hover:scale-105 active:scale-95"]: !isConnecting,
                        }
                    )}
                    style={{
                        background: "#FBAA31",
                        boxShadow:
                            "inset 2.22px 1.11px 4.43px 0px rgba(255, 255, 255, 0.25), 0px 0px 0px 1px rgba(0, 0, 0, 0.05)",
                        backdropFilter: "blur(4.43px)",
                    }}
                >
                    <div
                        className="absolute inset-0 rounded-full"
                        style={{
                            background: "#FFC267",
                        }}
                    />
                    <div className="relative flex h-full w-full items-center justify-center">
                        <svg
                            width="23"
                            height="23"
                            viewBox="0 0 23 23"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                            className="opacity-30"
                        >
                            <path
                                d="M10.5 2L12.5 10.5L21 12.5L12.5 14.5L10.5 23L8.5 14.5L0 12.5L8.5 10.5L10.5 2Z"
                                fill="white"
                            />
                        </svg>
                    </div>
                    {isConnecting && (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="h-6 w-6 animate-spin rounded-full border-2 border-white border-t-transparent" />
                        </div>
                    )}
                </button>
            </div>
        </div>
    );
}
