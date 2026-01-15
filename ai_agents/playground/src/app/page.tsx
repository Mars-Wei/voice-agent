"use client";

import React from "react";
import { useAppSelector, useAppDispatch } from "@/common";
import { apiStartService } from "@/common/request";
import AuthInitializer from "@/components/authInitializer";
import WelcomePage from "@/components/WelcomePage";
import ChatPage from "@/components/ChatPage";
import {
  setAgentConnected,
  setRoomConnected,
  setRtmConnected,
  setOptions,
  setSelectedGraphId,
} from "@/store/reducers/global";

export default function Home() {
  const [isConnecting, setIsConnecting] = React.useState(false);
  const dispatch = useAppDispatch();
  const agentConnected = useAppSelector((state) => state.global.agentConnected);
  const rtmConnected = useAppSelector((state) => state.global.rtmConnected);
  const roomConnected = useAppSelector((state) => state.global.roomConnected);
  const options = useAppSelector((state) => state.global.options);
  const selectedGraphId = useAppSelector(
    (state) => state.global.selectedGraphId
  );
  const graphList = useAppSelector((state) => state.global.graphList);

  const isConnected = agentConnected && rtmConnected && roomConnected;

  // Debug: log connection states
  React.useEffect(() => {
    console.log("[Home] Connection states:", {
      agentConnected,
      rtmConnected,
      roomConnected,
      isConnected,
    });
  }, [agentConnected, rtmConnected, roomConnected, isConnected]);

  // Auto-select "voice_assistant" graph if not selected
  React.useEffect(() => {
    if (
      typeof window !== "undefined" &&
      graphList.length > 0 &&
      !selectedGraphId
    ) {
      const voiceAssistantGraph = graphList.find(
        (g) => g.name === "voice_assistant"
      );
      if (voiceAssistantGraph) {
        const graphId = voiceAssistantGraph.graph_id || voiceAssistantGraph.name;
        dispatch(setSelectedGraphId(graphId));
      }
    }
  }, [graphList, selectedGraphId, dispatch]);

  const handleConnect = async () => {
    if (isConnecting || typeof window === "undefined") {
      return;
    }

    setIsConnecting(true);
    try {
      const { rtcManager } = await import("@/manager/rtc/rtc");
      const { rtmManager } = await import("@/manager/rtm");

      const { channel, userId } = options;

      // Ensure graph is selected (try to find by name if graph_id doesn't match)
      let selectedGraph = graphList.find(
        (graph) => graph.graph_id === selectedGraphId
      );

      // If not found by graph_id, try by name
      if (!selectedGraph) {
        selectedGraph = graphList.find((g) => g.name === "voice_assistant");
        if (selectedGraph) {
          const graphId = selectedGraph.graph_id || selectedGraph.name;
          dispatch(setSelectedGraphId(graphId));
        }
      }

      if (!selectedGraph) {
        console.error("Please select a graph first");
        setIsConnecting(false);
        return;
      }

      // Start agent service
      const res = await apiStartService({
        channel,
        userId,
        graphName: selectedGraph.name,
        language: "zh-CN",
        voiceType: "default",
      });

      if (res?.code != 0) {
        console.error(`Failed to start service: ${res?.msg}`);
        setIsConnecting(false);
        return;
      }

      dispatch(setAgentConnected(true));

      // Initialize RTC
      rtcManager.on("localTracksChanged", () => { });
      rtcManager.on("textChanged", () => { });
      rtcManager.on("remoteUserChanged", () => { });
      await rtcManager.createCameraTracks();
      await rtcManager.createMicrophoneAudioTrack();
      await rtcManager.join({ channel, userId });
      dispatch(
        setOptions({
          ...options,
          appId: rtcManager.appId ?? "",
          token: rtcManager.token ?? "",
        })
      );
      await rtcManager.publish();
      dispatch(setRoomConnected(true));

      // Initialize RTM - use the token from rtcManager
      const rtcAppId = rtcManager.appId;
      const rtcToken = rtcManager.token;

      console.log("[Home] Initializing RTM with:", {
        appId: rtcAppId,
        hasToken: !!rtcToken,
        channel,
        userId,
      });

      if (rtcAppId && rtcToken) {
        try {
          await rtmManager.init({
            channel,
            userId,
            appId: rtcAppId,
            token: rtcToken,
          });
          console.log("[Home] RTM initialized successfully");
          dispatch(setRtmConnected(true));
        } catch (error: any) {
          console.warn("[Home] RTM initialization failed, but continuing without RTM:", error);
          // RTM is optional - the app can work with RTC alone
          // Set RTM as connected anyway to allow page transition
          // Users can still interact via voice (RTC) even without RTM text messaging
          dispatch(setRtmConnected(true));

          // Show a non-blocking warning to the user
          if (error?.message?.includes("RTM service is not enabled")) {
            console.warn(
              "[Home] RTM service is not enabled in your Agora project. " +
              "Text messaging features will be unavailable, but voice features will work normally."
            );
          }
        }
      } else {
        console.warn("[Home] No RTC token available for RTM initialization");
        // Set RTM as connected anyway to allow page transition
        dispatch(setRtmConnected(true));
      }

      console.log("[Home] Connection setup complete, final states:", {
        agentConnected: true,
        rtmConnected: true,
        roomConnected: true,
      });

      setIsConnecting(false);
    } catch (error) {
      console.error("Connection error:", error);
      setIsConnecting(false);
    }
  };

  return (
    <AuthInitializer>
      {isConnected ? (
        <ChatPage />
      ) : (
        <WelcomePage onConnect={handleConnect} isConnecting={isConnecting} />
      )}
    </AuthInitializer>
  );
}
