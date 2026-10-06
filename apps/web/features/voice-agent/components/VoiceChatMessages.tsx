"use client";

import React, { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { MessageSquare, Sparkles } from "lucide-react";
import styles from "../../../styles/voice-agent.module.css";

export interface SentimentData {
  label: string;
  score: number;
  emoji: string;
}

export interface ChatMessage {
  id: string;
  speaker: "agent" | "user";
  text: string;
  sentiment?: SentimentData;
  timestamp?: number;
}

interface VoiceChatMessagesProps {
  messages: ChatMessage[];
  isConnected: boolean;
  status: string;
}

export const VoiceChatMessages: React.FC<VoiceChatMessagesProps> = ({
  messages,
  isConnected,
  status,
}) => {
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className={styles.chatPane}>
      <div className={styles.chatFeed} ref={scrollRef}>
        {messages.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyStateIcon}>
              <Sparkles size={28} />
            </div>
            <h4 style={{ fontSize: "15px", fontWeight: 700, margin: 0, color: "var(--foreground)" }}>
              {isConnected ? "Live Session Connected" : "Ready to Converse"}
            </h4>
            <p style={{ fontSize: "12.5px", margin: 0, color: "var(--foreground-muted)", lineHeight: 1.5 }}>
              {isConnected
                ? "Start speaking naturally into your microphone. Responses stream in real-time."
                : "Click 'START SESSION' below to begin high-speed voice interaction with Google Gemini Live."}
            </p>
          </div>
        ) : (
          messages.map((msg) => {
            const isAgent = msg.speaker === "agent";
            return (
              <div
                key={msg.id}
                className={`${styles.chatBubble} ${isAgent ? styles.agentBubble : styles.userBubble}`}
              >
                <div className={styles.bubbleHeader}>
                  <span className={styles.bubbleSender}>
                    {isAgent ? "Vedika (AI Tutor)" : "You"}
                  </span>
                  {!isAgent && msg.sentiment && (
                    <span className={styles.bubbleSentiment} title={`Score: ${msg.sentiment.score}`}>
                      {msg.sentiment.emoji} {msg.sentiment.label}
                    </span>
                  )}
                </div>

                <div style={{ wordBreak: "break-word" }}>
                  {isAgent ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.text}
                    </ReactMarkdown>
                  ) : (
                    <span>{msg.text}</span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
