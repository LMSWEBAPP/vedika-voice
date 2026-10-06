"use client";

import React, { useEffect, useRef, useState } from "react";
import { Mic, MicOff, Send, Bot, User, Volume2, Sparkles, Radio, Zap } from "lucide-react";
import { VoiceAgentView } from "../../voice-agent/components/VoiceAgentView";
import styles from "../../../styles/agent.module.css";

interface LiveVoiceTesterProps {
  campaignId: string;
  script: any;
}

export const LiveVoiceTester: React.FC<LiveVoiceTesterProps> = ({ campaignId, script }) => {
  const [engineMode, setEngineMode] = useState<"live" | "turn-based">("live");
  const [isConnected, setIsConnected] = useState(false);
  const [isMicActive, setIsMicActive] = useState(false);
  const [messages, setMessages] = useState<Array<{ speaker: string; text: string }>>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [aiSpeaking, setAiSpeaking] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  const stopCurrentAudio = () => {
    if (currentAudioRef.current) {
      try {
        currentAudioRef.current.pause();
        currentAudioRef.current.currentTime = 0;
      } catch (_) {}
      currentAudioRef.current = null;
    }
    setAiSpeaking(false);
  };

  const playNeuralAudio = (base64Audio: string) => {
    if (!base64Audio) return;
    try {
      stopCurrentAudio();
      const audioUrl = `data:audio/mp3;base64,${base64Audio}`;
      const audio = new Audio(audioUrl);
      currentAudioRef.current = audio;

      audio.onplay = () => {
        setAiSpeaking(true);
      };

      audio.onended = () => {
        setAiSpeaking(false);
        currentAudioRef.current = null;
      };

      audio.onerror = (e) => {
        console.warn("Audio playback issue:", e);
        setAiSpeaking(false);
        currentAudioRef.current = null;
      };

      audio.play().catch((playErr) => {
        console.warn("Audio play prevented or interrupted:", playErr);
        setAiSpeaking(false);
      });
    } catch (err) {
      console.error("Failed to play neural audio", err);
      setAiSpeaking(false);
    }
  };

  const startSession = () => {
    const targetCampaign = campaignId || "sandbox";
    const wsUrl = `ws://localhost:8000/ws/agent/test/${targetCampaign}`;
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
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last && last.speaker === "ai") {
              return [...prev.slice(0, -1), { speaker: "ai", text: last.text + " " + data.text }];
            }
            return [...prev, { speaker: "ai", text: data.text }];
          });
        } else if (data.type === "ai_audio") {
          // Play the ultra-realistic human neural speech
          if (data.data) {
            playNeuralAudio(data.data);
          }
        } else if (data.type === "turn_complete") {
          const turnData = data.data || {};
          if (turnData.audio) {
            playNeuralAudio(turnData.audio);
          }
        }
      } catch (err) {
        console.error("WS message parse error", err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      setIsMicActive(false);
      stopCurrentAudio();
    };
  };

  const recognitionRef = useRef<any>(null);

  const endSession = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    stopMic();
    stopCurrentAudio();
    setIsConnected(false);
  };

  const startMic = async () => {
    try {
      setIsMicActive(true);

      // Start Browser Speech Recognition if supported
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = false;
        recognition.lang = "en-IN";
        recognition.onresult = (e: any) => {
          const transcript = e.results[e.results.length - 1][0].transcript;
          if (transcript.trim() && wsRef.current?.readyState === WebSocket.OPEN) {
            stopCurrentAudio();
            wsRef.current.send(JSON.stringify({ type: "text", text: transcript.trim() }));
            setMessages((prev) => [...prev, { speaker: "user", text: transcript.trim() }]);
          }
        };
        recognition.onerror = () => {};
        recognition.start();
        recognitionRef.current = recognition;
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = async (e) => {
        if (e.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          const buffer = await e.data.arrayBuffer();
          let binary = "";
          const bytes = new Uint8Array(buffer);
          for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
          }
          const base64Audio = btoa(binary);
          wsRef.current.send(JSON.stringify({ type: "audio", data: base64Audio }));
        }
      };

      recorder.start(250);
    } catch (err) {
      console.warn("Audio hardware stream notice:", err);
    }
  };

  const stopMic = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (_) {}
      recognitionRef.current = null;
    }
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

    stopCurrentAudio();
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

      {/* Engine Mode Pill Toggle */}
      <div
        style={{
          display: "flex",
          background: "var(--background)",
          padding: "4px",
          borderRadius: "var(--radius-full)",
          border: "1px solid var(--border)",
          gap: "4px",
          marginTop: "12px",
          marginBottom: "14px",
        }}
      >
        <button
          type="button"
          onClick={() => {
            endSession();
            setEngineMode("live");
          }}
          style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "6px",
            padding: "8px 14px",
            borderRadius: "var(--radius-full)",
            fontSize: "12px",
            fontWeight: 700,
            border: "none",
            cursor: "pointer",
            background: engineMode === "live" ? "var(--primary)" : "transparent",
            color: engineMode === "live" ? "#ffffff" : "var(--foreground-muted)",
            boxShadow: engineMode === "live" ? "0 2px 8px rgba(79, 70, 229, 0.4)" : "none",
            transition: "all 0.15s ease",
          }}
        >
          <Zap size={14} color={engineMode === "live" ? "#39FF14" : "currentColor"} />
          <span>Gemini Multimodal Live (PCM Audio)</span>
        </button>
        <button
          type="button"
          onClick={() => setEngineMode("turn-based")}
          style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "6px",
            padding: "8px 14px",
            borderRadius: "var(--radius-full)",
            fontSize: "12px",
            fontWeight: 600,
            border: "none",
            cursor: "pointer",
            background: engineMode === "turn-based" ? "var(--secondary)" : "transparent",
            color: engineMode === "turn-based" ? "#ffffff" : "var(--foreground-muted)",
            transition: "all 0.15s ease",
          }}
        >
          <Radio size={14} />
          <span>Turn-Based Studio</span>
        </button>
      </div>

      {engineMode === "live" ? (
        <VoiceAgentView
          inline={true}
          persona={script?.persona}
          objective={script?.objective}
          voiceName={script?.voice_name || "Zephyr"}
          sessionId={`camp_${campaignId || "sandbox"}`}
        />
      ) : (
        <>
          {/* Voice Status & Mode Badge */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              fontSize: "12px",
              background: "rgba(99, 102, 241, 0.08)",
              padding: "8px 12px",
              borderRadius: "var(--radius-md)",
              border: "1px solid rgba(99, 102, 241, 0.2)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--primary)" }}>
              <Volume2 size={14} />
              <span>Voice: <strong>{script?.voice_name || "Madhu"}</strong> (Neural Human Audio)</span>
            </div>
            {aiSpeaking ? (
              <span style={{ color: "#34d399", fontWeight: 600, display: "flex", alignItems: "center", gap: "6px" }}>
                <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#34d399", display: "inline-block" }}></span>
                Speaking...
              </span>
            ) : isMicActive ? (
              <span style={{ color: "#f87171", fontWeight: 600 }}>Listening...</span>
            ) : (
              <span style={{ color: "var(--foreground-muted)" }}>Ready</span>
            )}
          </div>

      {/* Waveform Visualizer Canvas */}
      <div className={styles.waveformCanvas}>
        {[...Array(24)].map((_, i) => (
          <div
            key={i}
            className={`${styles.waveBar} ${(isMicActive || aiSpeaking) ? styles.waveBarActive : ""}`}
            style={{
              animationDelay: `${(i % 8) * 0.1}s`,
              height: isMicActive || aiSpeaking ? `${Math.max(8, (i * 7) % 40)}px` : "6px",
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
        </>
      )}
    </div>
  );
};
