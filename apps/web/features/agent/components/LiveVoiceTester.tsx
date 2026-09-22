"use client";

import React, { useEffect, useRef, useState } from "react";
import { Mic, MicOff, Send, Bot, User, Volume2, Sparkles } from "lucide-react";
import styles from "../../../styles/agent.module.css";

interface LiveVoiceTesterProps {
  campaignId: string;
  script: any;
}

export const LiveVoiceTester: React.FC<LiveVoiceTesterProps> = ({ campaignId, script }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isMicActive, setIsMicActive] = useState(false);
  const [messages, setMessages] = useState<Array<{ speaker: string; text: string }>>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [aiSpeaking, setAiSpeaking] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  const startSession = () => {
    if (!campaignId) return;

    const wsUrl = `ws://localhost:8000/ws/agent/test/${campaignId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setMessages([]);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "ai_text") {
          setAiSpeaking(true);
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last && last.speaker === "ai") {
              return [...prev.slice(0, -1), { speaker: "ai", text: last.text + " " + data.text }];
            }
            return [...prev, { speaker: "ai", text: data.text }];
          });
        } else if (data.type === "turn_complete") {
          setAiSpeaking(false);
        } else if (data.type === "ai_audio") {
          // Play simulated audio chime/speech if audioContext available
          playAudioTone();
        }
      } catch (err) {
        console.error("WS message parse error", err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      setIsMicActive(false);
      setAiSpeaking(false);
    };
  };

  const endSession = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    stopMic();
    setIsConnected(false);
  };

  const playAudioTone = () => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      const ctx = audioContextRef.current;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(440, ctx.currentTime);
      gain.gain.setValueAtTime(0.05, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.2);
    } catch (_) {}
  };

  const startMic = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setIsMicActive(true);

      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = async (e) => {
        if (e.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          const buffer = await e.data.arrayBuffer();
          // Convert array buffer to base64
          let binary = "";
          const bytes = new Uint8Array(buffer);
          for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
          }
          const base64Audio = btoa(binary);
          wsRef.current.send(JSON.stringify({ type: "audio", data: base64Audio }));
        }
      };

      recorder.start(250); // 250ms chunks
    } catch (err) {
      alert("Microphone access could not be initialized. You can still test via text below!");
    }
  };

  const stopMic = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach((t) => t.stop());
      mediaRecorderRef.current = null;
    }
    setIsMicActive(false);
  };

  const handleSendText = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !wsRef.current) return;

    wsRef.current.send(JSON.stringify({ type: "text", text: inputMessage.trim() }));
    setMessages((prev) => [...prev, { speaker: "user", text: inputMessage.trim() }]);
    setInputMessage("");
  };

  useEffect(() => {
    return () => {
      endSession();
    };
  }, []);

  return (
    <div className={styles.testerContainer}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h3 style={{ fontSize: "16px", fontWeight: 700, display: "flex", alignItems: "center", gap: "8px" }}>
            <Sparkles size={16} color="var(--primary)" />
            <span>Live Voice Agent Tester</span>
          </h3>
          <p style={{ fontSize: "12px", color: "var(--foreground-muted)", marginTop: "2px" }}>
            Speak via your microphone or type to test conversation turns in real-time
          </p>
        </div>

        <div>
          {isConnected ? (
            <span className="badge badge-success">Connected</span>
          ) : (
            <span className="badge badge-neutral">Offline</span>
          )}
        </div>
      </div>

      {/* Waveform Visualizer Canvas */}
      <div className={styles.waveformCanvas}>
        {[...Array(24)].map((_, i) => (
          <div
            key={i}
            className={`${styles.waveBar} ${(isMicActive || aiSpeaking) ? styles.waveBarActive : ""}`}
            style={{
              animationDelay: `${(i % 8) * 0.1}s`,
              height: isMicActive || aiSpeaking ? `${Math.max(6, (i * 7) % 36)}px` : "6px",
            }}
          />
        ))}
      </div>

      {/* Control Buttons */}
      <div style={{ display: "flex", gap: "10px" }}>
        {!isConnected ? (
          <button onClick={startSession} className="btn btn-primary" style={{ flex: 1 }}>
            <Volume2 size={16} />
            <span>Connect Voice Agent</span>
          </button>
        ) : (
          <>
            <button
              onClick={isMicActive ? stopMic : startMic}
              className={`btn ${isMicActive ? "btn-danger" : "btn-primary"}`}
              style={{ flex: 1 }}
            >
              {isMicActive ? <MicOff size={16} /> : <Mic size={16} />}
              <span>{isMicActive ? "Mute Mic" : "Enable Mic"}</span>
            </button>
            <button onClick={endSession} className="btn btn-secondary btn-sm">
              Disconnect
            </button>
          </>
        )}
      </div>

      {/* Transcript Chat Feed */}
      <div
        style={{
          height: "280px",
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
          background: "var(--background-secondary)",
          padding: "14px",
          borderRadius: "var(--radius-md)",
          border: "1px solid var(--border)",
        }}
      >
        {messages.length === 0 ? (
          <div style={{ margin: "auto", textAlign: "center", color: "var(--foreground-muted)", fontSize: "13px" }}>
            {isConnected ? "Agent connected. Say something or type below!" : "Click 'Connect Voice Agent' to start testing."}
          </div>
        ) : (
          messages.map((m, idx) => {
            const isAi = m.speaker === "ai";
            return (
              <div
                key={idx}
                style={{
                  alignSelf: isAi ? "flex-start" : "flex-end",
                  background: isAi ? "rgba(79, 70, 229, 0.15)" : "rgba(6, 182, 212, 0.15)",
                  border: `1px solid ${isAi ? "rgba(79, 70, 229, 0.3)" : "rgba(6, 182, 212, 0.3)"}`,
                  borderRadius: "var(--radius-md)",
                  padding: "8px 12px",
                  maxWidth: "85%",
                  fontSize: "13px",
                }}
              >
                <div style={{ fontSize: "10px", fontWeight: 700, color: isAi ? "#818cf8" : "#22d3ee", marginBottom: "2px" }}>
                  {isAi ? "AI Agent" : "You (Tester)"}
                </div>
                <div>{m.text}</div>
              </div>
            );
          })
        )}
      </div>

      {/* Interactive Text Input */}
      <form onSubmit={handleSendText} style={{ display: "flex", gap: "8px" }}>
        <input
          type="text"
          className="form-input"
          placeholder={isConnected ? "Type a response to the AI agent..." : "Connect first to chat"}
          disabled={!isConnected}
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          style={{ flex: 1, fontSize: "13px" }}
        />
        <button type="submit" disabled={!isConnected || !inputMessage.trim()} className="btn btn-primary btn-sm">
          <Send size={14} />
        </button>
      </form>
    </div>
  );
};
