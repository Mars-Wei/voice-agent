"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { useMultibandTrackVolume } from "@/common";
import type { IMicrophoneAudioTrack } from "agora-rtc-sdk-ng";

interface AudioWaveformProps {
    audioTrack?: IMicrophoneAudioTrack;
    className?: string;
}

export default function AudioWaveform({
    audioTrack,
    className,
}: AudioWaveformProps) {
    // Use more bands for smoother waveform
    const frequencyBands = useMultibandTrackVolume(
        audioTrack,
        40, // More bands for smoother curve
        50, // Lower frequency range
        8000 // Higher frequency range for more detail
    );

    // Calculate if there's significant audio activity
    const hasAudioActivity = React.useMemo(() => {
        if (frequencyBands.length === 0) return false;

        // Calculate max volume across all bands
        const maxVolume = frequencyBands.reduce((max, band) => {
            if (band.length === 0) return max;
            const bandMax = Math.max(...Array.from(band).map(v => Math.abs(v)));
            return Math.max(max, bandMax);
        }, 0);

        // Lower threshold for better sensitivity (normalized values are typically 0-1)
        // Using max instead of average for better responsiveness
        return maxVolume > 0.005; // Very low threshold to catch any audio
    }, [frequencyBands]);

    // Create smooth waveform path using cubic bezier curves
    const createWaveLayer = (
        offset: number,
        color: string,
        opacity: number,
        scale: number = 1
    ) => {
        const width = 800;
        const height = 100;
        const centerY = height / 2;

        if (frequencyBands.length === 0) {
            // Return flat line when no frequency data
            return (
                <path
                    d={`M 0,${centerY} L ${width},${centerY}`}
                    stroke={color}
                    strokeWidth="2"
                    fill="none"
                    opacity={opacity * 0.3}
                />
            );
        }

        const points = frequencyBands.length;

        if (!hasAudioActivity) {
            // Return flat line when no audio
            return (
                <path
                    d={`M 0,${centerY} L ${width},${centerY}`}
                    stroke={color}
                    strokeWidth="2"
                    fill="none"
                    opacity={opacity * 0.3}
                    style={{
                        transition: "opacity 0.5s ease-out",
                    }}
                />
            );
        }

        // Generate control points for smooth bezier curve
        const controlPoints: Array<{ x: number; y: number }> = [];
        const stepX = width / (points - 1);

        for (let i = 0; i < points; i++) {
            const band = frequencyBands[i];
            const avgFreq =
                band.length > 0
                    ? Array.from(band).reduce((a, b) => a + Math.abs(b), 0) / band.length
                    : 0;

            // Normalize and scale the amplitude
            // The frequency values are typically negative dB, so we need to convert them
            // Normalize from dB range (roughly -100 to 0) to 0-1 range
            const normalized = Math.min(1, Math.max(0, (avgFreq + 100) / 100));
            const baseAmplitude = normalized * 45 * scale;

            // Create smooth wave pattern with sine-like variation
            const wavePhase = ((i + offset) * 2 * Math.PI) / points;
            const amplitude = baseAmplitude * (0.8 + 0.2 * Math.sin(wavePhase * 2));
            const y = centerY + Math.sin(wavePhase * 3) * amplitude;

            controlPoints.push({
                x: i * stepX,
                y: y,
            });
        }

        // Create smooth bezier curve path
        let path = `M ${controlPoints[0].x},${controlPoints[0].y} `;

        for (let i = 1; i < controlPoints.length; i++) {
            const prev = controlPoints[i - 1];
            const curr = controlPoints[i];
            const next = controlPoints[Math.min(i + 1, controlPoints.length - 1)];

            // Calculate control points for smooth bezier curve
            const cp1x = prev.x + (curr.x - prev.x) * 0.5;
            const cp1y = prev.y;
            const cp2x = curr.x - (next.x - curr.x) * 0.5;
            const cp2y = curr.y;

            if (i === 1) {
                path += `Q ${cp1x},${cp1y} ${curr.x},${curr.y} `;
            } else if (i < controlPoints.length - 1) {
                path += `C ${prev.x + (curr.x - prev.x) * 0.3},${prev.y} ${curr.x - (curr.x - prev.x) * 0.3},${curr.y} ${curr.x},${curr.y} `;
            } else {
                path += `L ${curr.x},${curr.y} `;
            }
        }

        // Close the path to create filled wave
        path += `L ${width},${centerY} L 0,${centerY} Z`;

        return (
            <path
                d={path}
                fill={color}
                opacity={opacity}
                style={{
                    transition: hasAudioActivity ? "opacity 0.3s ease-out, d 0.1s linear" : "opacity 0.5s ease-out",
                }}
            />
        );
    };

    // Debug logging
    React.useEffect(() => {
        console.log("[AudioWaveform] audioTrack:", audioTrack ? "exists" : "null");
        console.log("[AudioWaveform] frequencyBands.length:", frequencyBands.length);
        console.log("[AudioWaveform] hasAudioActivity:", hasAudioActivity);
    }, [audioTrack, frequencyBands.length, hasAudioActivity]);

    // Always render something, even if no audio track
    return (
        <div
            className={cn("flex w-full items-center justify-center", className)}
            style={{
                height: "100px",
                minHeight: "100px",
                opacity: hasAudioActivity ? 1 : (audioTrack ? 0.5 : 0.3),
                transition: "opacity 0.5s ease-out",
            }}
        >
            <svg
                width="800"
                height="100"
                viewBox="0 0 800 100"
                preserveAspectRatio="none"
                style={{
                    width: "100%",
                    maxWidth: "600px",
                    height: "100px",
                }}
            >
                {audioTrack ? (
                    <>
                        {/* Multiple layered waves for the colorful effect */}
                        {createWaveLayer(0, "#FF6B9D", 0.7, 1.0)}
                        {createWaveLayer(5, "#4ECDC4", 0.6, 0.9)}
                        {createWaveLayer(10, "#45B7D1", 0.5, 0.8)}
                        {createWaveLayer(-5, "#FFA07A", 0.4, 0.7)}

                        {/* Fallback flat line when no audio */}
                        {!hasAudioActivity && frequencyBands.length > 0 && (
                            <line
                                x1="0"
                                y1="50"
                                x2="800"
                                y2="50"
                                stroke="#CCCCCC"
                                strokeWidth="2"
                                opacity="0.5"
                            />
                        )}
                    </>
                ) : (
                    /* Show placeholder when no audio track */
                    <line
                        x1="0"
                        y1="50"
                        x2="800"
                        y2="50"
                        stroke="#CCCCCC"
                        strokeWidth="2"
                        opacity="0.3"
                    />
                )}
            </svg>
        </div>
    );
}