import { Bot, Brain, MessageCircleQuestion } from "lucide-react";
import * as React from "react";
import {
  GRAPH_OPTIONS,
  isRagGraph,
  LANGUAGE_OPTIONS,
  useAppDispatch,
  useAppSelector,
  useAutoScroll,
} from "@/common";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { EMessageDataType, EMessageType, type IChatItem } from "@/types";

export default function MessageList(props: { className?: string }) {
  const { className } = props;

  const chatItems = useAppSelector((state) => state.global.chatItems);

  const containerRef = React.useRef<HTMLDivElement>(null);

  // Auto scroll when new messages arrive
  React.useEffect(() => {
    if (containerRef.current) {
      // Use requestAnimationFrame to ensure DOM is updated
      requestAnimationFrame(() => {
        if (containerRef.current) {
          containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
      });
    }
  }, [chatItems.length, chatItems]);

  // Also use the useAutoScroll hook for DOM mutations
  useAutoScroll(containerRef);

  console.log("[MessageList] Rendering chat items:", chatItems.length, chatItems);

  return (
    <div
      ref={containerRef}
      className={cn("flex w-full flex-col", className)}
      style={{
        height: "100%",
        overflowY: "auto",
        scrollBehavior: "smooth",
      }}
    >
      {chatItems.length === 0 ? (
        <div className="flex h-full w-full items-center justify-center text-gray-400">
          <p className="text-xl">暂无消息</p>
        </div>
      ) : (
        chatItems.map((item, index) => {
          return <MessageItem data={item} key={`${item.time}-${index}`} />;
        })
      )}
    </div>
  );
}

export function MessageItem(props: { data: IChatItem }) {
  const { data } = props;
  const isUser = data.type === EMessageType.USER;

  return (
    <div
      className={cn("flex w-full items-end gap-4 mb-4", {
        "justify-end": isUser,
        "justify-start": !isUser,
      })}
    >
      <div
        className={cn("max-w-[70%] rounded-3xl px-10 py-6", {
          "rounded-br-none": isUser,
          "rounded-bl-none": !isUser,
        })}
        style={{
          background: isUser
            ? "#886A86"
            : "rgba(255, 255, 255, 0.52)",
          backdropFilter: "blur(95.2px)",
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.1)",
        }}
      >
        {data.data_type === EMessageDataType.IMAGE ? (
          <img src={data.text} alt="chat" className="w-full rounded-lg" />
        ) : (
          <p
            className={cn("text-2xl leading-relaxed whitespace-pre-wrap break-words", {
              "text-white": isUser,
            })}
            style={{
              fontFamily: "PingFang SC",
              fontWeight: 500,
              color: isUser ? "#FFFFFF" : "#6A5B77",
              textAlign: isUser ? "right" : "left",
              lineHeight: "1.6",
            }}
          >
            {data.text}
          </p>
        )}
      </div>
    </div>
  );
}
