"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Mic,
  MicOff,
  Radio,
  Sparkles,
  Volume2,
  VolumeX,
  RotateCcw,
  Send,
  AlertCircle,
  Globe,
  PhoneCall,
  PhoneOff,
  Building2,
  User,
  Target,
  Briefcase,
  ChevronDown,
  ChevronUp,
  FileSpreadsheet,
  Zap,
} from "lucide-react";
import { VoiceRobotVisualizer } from "./VoiceRobotVisualizer";
import { VoiceChatMessages, ChatMessage, SentimentData } from "./VoiceChatMessages";
import { LeadsSpreadsheetGrid, SpreadsheetLead, INITIAL_LEADS } from "../../leads/components/LeadsSpreadsheetGrid";
import styles from "../../../styles/voice-agent.module.css";

type ConnectionStatus = "disconnected" | "connecting" | "connected" | "tutor-speaking" | "agent-speaking" | "error";

interface VoiceAgentViewProps {
  inline?: boolean;
  onClose?: () => void;
  initialLanguage?: string;
  initialSubject?: string;
  initialClientName?: string;
  initialBusinessName?: string;
  initialBusinessType?: string;
  initialPitchGoal?: string;
  persona?: string;
  objective?: string;
  voiceName?: string;
  sessionId?: string;
  userId?: string;
}

export const VoiceAgentView: React.FC<VoiceAgentViewProps> = ({
  inline = false,
  onClose,
  initialLanguage = "all",
  initialClientName,
  initialBusinessName,
  initialBusinessType,
  initialPitchGoal,
  persona,
  objective,
  voiceName = "Zephyr",
  sessionId,
  userId,
}) => {
  // Connection and State
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("disconnected");
  const [statusMessage, setStatusMessage] = useState<string>("Select a prospect and click CALL PROSPECT to start the pitch");
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [currentSentiment, setCurrentSentiment] = useState<SentimentData | null>(null);

  // Settings & Language
  const [selectedLanguage, setSelectedLanguage] = useState<string>(initialLanguage);

  // Prospect Client Profile State
  const [activeSpreadsheetLeadId, setActiveSpreadsheetLeadId] = useState<string>(INITIAL_LEADS[0].id);
  const [clientName, setClientName] = useState<string>(initialClientName || INITIAL_LEADS[0].name);
  const [businessName, setBusinessName] = useState<string>(initialBusinessName || INITIAL_LEADS[0].company);
  const [businessType, setBusinessType] = useState<string>(initialBusinessType || INITIAL_LEADS[0].industry);
  const [pitchGoal, setPitchGoal] = useState<string>(initialPitchGoal || INITIAL_LEADS[0].pitchGoal);
  const [leadNotes, setLeadNotes] = useState<string>(INITIAL_LEADS[0].notes);
  const [leadCity, setLeadCity] = useState<string>(INITIAL_LEADS[0].city);
  const [leadDealValue, setLeadDealValue] = useState<string>(INITIAL_LEADS[0].dealValue);
  const [leadPhone, setLeadPhone] = useState<string>(INITIAL_LEADS[0].phone);
  const [agentName, setAgentName] = useState<string>("Aarav from Veyra Software Solutions");

  // Chat Feed
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState<string>("");

  // Refs for Web Audio API & WebSocket
  const wsRef = useRef<WebSocket | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

  const isMutedRef = useRef<boolean>(false);
  isMutedRef.current = isMuted;

  // Queue of active audio buffer source nodes for gapless playback & barge-in cutoff
  const audioSourcesQueueRef = useRef<AudioBufferSourceNode[]>([]);
  const nextPlayTimeRef = useRef<number>(0);

  /**
   * Handle Spreadsheet Lead Selection
   */
  const handleSelectSpreadsheetLead = (lead: SpreadsheetLead) => {
    setActiveSpreadsheetLeadId(lead.id);
    setClientName(lead.name);
    setBusinessName(lead.company);
    setBusinessType(lead.industry);
    setPitchGoal(lead.pitchGoal);
    setLeadNotes(lead.notes);
    setLeadCity(lead.city);
    setLeadDealValue(lead.dealValue);
    setLeadPhone(lead.phone);
  };

  /**
   * Stop all active audio playbacks immediately (Barge-in / Interruption)
   */
  const stopAllAudioPlaybacks = useCallback(() => {
    audioSourcesQueueRef.current.forEach((source) => {
      try {
        source.stop();
        source.disconnect();
      } catch (_) {}
    });
    audioSourcesQueueRef.current = [];
    nextPlayTimeRef.current = 0;
  }, []);

  /**
   * Decode 24kHz Int16 PCM Base64 chunk and schedule gapless playback via Web Audio API
   */
  const playPcmAudioChunk = useCallback((base64Data: string) => {
    if (!audioCtxRef.current || isMutedRef.current) return;

    try {
      const audioCtx = audioCtxRef.current;

      // Ensure AudioContext is running
      if (audioCtx.state === "suspended") {
        audioCtx.resume();
      }

      // 1. Decode base64 to binary ArrayBuffer
      const binaryString = atob(base64Data);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      // 2. Interpret as Int16 signed integers (Little-Endian)
      const int16Samples = new Int16Array(bytes.buffer);

      // 3. Create AudioBuffer at Gemini Live output sample rate (24000 Hz)
      const audioBuffer = audioCtx.createBuffer(1, int16Samples.length, 24000);
      const channelData = audioBuffer.getChannelData(0);

      // 4. Normalize Int16 [-32768, 32767] to Float32 [-1.0, 1.0]
      for (let i = 0; i < int16Samples.length; i++) {
        channelData[i] = int16Samples[i] / 32768.0;
      }

      // 5. Create AudioBufferSourceNode
      const bufferSource = audioCtx.createBufferSource();
      bufferSource.buffer = audioBuffer;
      bufferSource.connect(audioCtx.destination);

      audioSourcesQueueRef.current.push(bufferSource);

      bufferSource.onended = () => {
        audioSourcesQueueRef.current = audioSourcesQueueRef.current.filter((src) => src !== bufferSource);
        if (audioSourcesQueueRef.current.length === 0) {
          setConnectionStatus("connected");
          setStatusMessage("Agent listening... Respond as the client to test objections.");
        }
      };

      // 6. Schedule gapless sequential playback with 50ms safety jitter buffer
      const now = audioCtx.currentTime;
      if (nextPlayTimeRef.current < now) {
        nextPlayTimeRef.current = now + 0.05;
      }

      setConnectionStatus("agent-speaking");
      setStatusMessage(`Aarav is speaking to ${clientName}...`);
      bufferSource.start(nextPlayTimeRef.current);
      nextPlayTimeRef.current += audioBuffer.duration;
    } catch (err) {
      console.warn("PCM audio playback scheduling error:", err);
    }
  }, [clientName]);

  /**
   * Initialize microphone capture at 16kHz PCM Little-Endian
   */
  const startMicrophone = async () => {
    try {
      // 1. Request microphone with native hardware AEC and noise suppression
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      micStreamRef.current = stream;

      // 2. Initialize AudioContext at exactly 16,000 Hz
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 16000,
      });
      audioCtxRef.current = audioCtx;

      // 3. Create MediaStreamSourceNode
      const source = audioCtx.createMediaStreamSource(stream);
      sourceRef.current = source;

      // 4. Create ScriptProcessorNode (bufferSize=4096 gives ~256ms packets at 16kHz)
      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      source.connect(processor);
      processor.connect(audioCtx.destination);

      processor.onaudioprocess = (e) => {
        if (isMutedRef.current) return;
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

        const inputData = e.inputBuffer.getChannelData(0);

        // Convert Float32 [-1.0, 1.0] to Int16 Little-Endian signed PCM
        const pcmBuffer = new ArrayBuffer(inputData.length * 2);
        const dataView = new DataView(pcmBuffer);

        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]));
          dataView.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
        }

        // Base64 encode PCM packet
        let binary = "";
        const bytes = new Uint8Array(pcmBuffer);
        const len = bytes.byteLength;
        for (let i = 0; i < len; i++) {
          binary += String.fromCharCode(bytes[i]);
        }
        const base64Data = btoa(binary);

        wsRef.current.send(JSON.stringify({ type: "audio", data: base64Data }));
      };
    } catch (err: any) {
      console.error("Microphone hardware acquisition error:", err);
      setStatusMessage(`Microphone error: ${err.message || "Permission denied"}`);
      setConnectionStatus("error");
    }
  };

  /**
   * Stop microphone and release Web Audio API resources
   */
  const stopMicrophone = () => {
    if (processorRef.current) {
      try {
        processorRef.current.disconnect();
      } catch (_) {}
      processorRef.current = null;
    }
    if (sourceRef.current) {
      try {
        sourceRef.current.disconnect();
      } catch (_) {}
      sourceRef.current = null;
    }
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((track) => track.stop());
      micStreamRef.current = null;
    }
    if (audioCtxRef.current) {
      try {
        audioCtxRef.current.close();
      } catch (_) {}
      audioCtxRef.current = null;
    }
  };

  /**
   * Append or update agent transcript tokens
   */
  const appendAgentTranscript = (text: string) => {
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.speaker === "agent") {
        return [
          ...prev.slice(0, -1),
          { ...last, text: last.text + text },
        ];
      }
      return [
        ...prev,
        {
          id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,
          speaker: "agent",
          text,
          timestamp: Date.now(),
        },
      ];
    });
  };

  /**
   * Append user transcript with real-time sentiment
   */
  const appendUserTranscript = (text: string, sentiment?: SentimentData) => {
    if (sentiment) {
      setCurrentSentiment(sentiment);
    }
    setMessages((prev) => [
      ...prev,
      {
        id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,
        speaker: "user",
        text,
        sentiment,
        timestamp: Date.now(),
      },
    ]);
  };

  /**
   * Connect to Gemini Live WebSocket Voice Server
   */
  const startSession = async () => {
    stopAllAudioPlaybacks();
    setConnectionStatus("connecting");
    setStatusMessage(`Dialing ${clientName} at ${businessName}...`);

    try {
      // Determine WebSocket Host URL
      const envWs = process.env.NEXT_PUBLIC_VOICE_WS_URL;
      let wsBase = envWs || "ws://localhost:5055/api/ws";

      if (!envWs && typeof window !== "undefined") {
        const isSecure = window.location.protocol === "https:";
        const host = window.location.hostname || "localhost";
        wsBase = `${isSecure ? "wss" : "ws"}://${host}:5055/api/ws`;
      }

      const activeSid = sessionId || `session_${Date.now().toString(36)}`;
      const activeUid = userId || `user_${Date.now().toString(36).slice(-4)}`;

      const params = new URLSearchParams({
        language: selectedLanguage,
        clientName,
        businessName,
        businessType,
        pitchGoal,
        agentName,
        sessionId: activeSid,
        userId: activeUid,
        voiceName,
        proactiveGreeting: "true",
        notes: leadNotes || "",
        city: leadCity || "",
        dealValue: leadDealValue || "",
        phone: leadPhone || "",
      });

      if (persona) params.append("persona", persona);
      if (objective) params.append("objective", objective);

      const wsUrl = `${wsBase}?${params.toString()}`;
      console.log("[VoiceAgentView] Connecting Outbound Call to:", wsUrl);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      // 12-second connection timeout guard
      const connectionTimer = setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          ws.close();
          setConnectionStatus("error");
          setStatusMessage("Connection timed out. Ensure voice-server.js is running on port 5055.");
        }
      }, 12000);

      ws.onopen = async () => {
        clearTimeout(connectionTimer);
        setConnectionStatus("connected");
        setStatusMessage(`Call connected! Dialing ${clientName} (${businessName})...`);
        await startMicrophone();
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          switch (msg.type) {
            case "status":
              setStatusMessage(msg.message);
              if (msg.status === "connected") setConnectionStatus("connected");
              break;

            case "audio":
              // 24kHz PCM chunk from Gemini Live
              if (msg.data) {
                playPcmAudioChunk(msg.data);
              }
              break;

            case "interrupted":
              // Barge-in: client spoke while AI was speaking
              console.log("[VoiceAgentView] Client spoke. Cutting off agent speech.");
              stopAllAudioPlaybacks();
              setConnectionStatus("connected");
              setStatusMessage("Agent paused. Listening to client...");
              break;

            case "agent-transcription":
              if (msg.text) {
                appendAgentTranscript(msg.text);
              }
              break;

            case "user-transcription":
              if (msg.text) {
                appendUserTranscript(msg.text, msg.sentiment);
              }
              break;

            case "error":
              setStatusMessage(msg.message || "Voice Server error.");
              setConnectionStatus("error");
              break;

            default:
              break;
          }
        } catch (e) {
          console.warn("Message parsing error:", e);
        }
      };

      ws.onerror = (err) => {
        console.error("WebSocket error:", err);
        clearTimeout(connectionTimer);
        setConnectionStatus("error");
        setStatusMessage("WebSocket connection failed. Verify voice server is running.");
      };

      ws.onclose = () => {
        clearTimeout(connectionTimer);
        setConnectionStatus("disconnected");
        setStatusMessage("Call ended. Select a prospect and click CALL PROSPECT to start another pitch.");
        stopMicrophone();
        stopAllAudioPlaybacks();
      };
    } catch (err: any) {
      console.error("Session start error:", err);
      setConnectionStatus("error");
      setStatusMessage(`Failed to connect: ${err.message || "Unknown error"}`);
    }
  };

  /**
   * End session and disconnect
   */
  const endSession = () => {
    if (wsRef.current) {
      try {
        wsRef.current.send(JSON.stringify({ type: "end" }));
      } catch (_) {}
      wsRef.current.close();
      wsRef.current = null;
    }
    stopMicrophone();
    stopAllAudioPlaybacks();
    setConnectionStatus("disconnected");
    setStatusMessage("Call ended.");
  };

  /**
   * Toggle microphone mute state
   */
  const handleToggleMute = () => {
    setIsMuted((prev) => !prev);
  };

  /**
   * Clear chat messages
   */
  const handleClearMessages = () => {
    setMessages([]);
  };

  /**
   * Send text fallback
   */
  const handleSendText = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    const text = inputText.trim();
    wsRef.current.send(JSON.stringify({ type: "text", text }));
    appendUserTranscript(text);
    setInputText("");
  };

  // Cleanup on component unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      stopMicrophone();
      stopAllAudioPlaybacks();
    };
  }, [stopAllAudioPlaybacks]);

  const isConnected =
    connectionStatus === "connected" ||
    connectionStatus === "tutor-speaking" ||
    connectionStatus === "agent-speaking";

  return (
    <div className={`${styles.voiceContainer} ${!inline ? styles.voiceContainerFullscreen : ""}`}>
      {/* Header Bar */}
      <div className={styles.voiceHeader}>
        <div className={styles.headerLeft}>
          <div className={styles.avatarBadge}>
            <Radio size={22} color="var(--primary)" />
          </div>
          <div className={styles.titleArea}>
            <h2>
              <span>Veyra Voice Outbound Studio</span>
              <Sparkles size={16} color="#39FF14" />
            </h2>
            <p>B2B Software & Website Sales Pitch Engine • Gemini Multimodal Live API</p>
          </div>
        </div>

        {/* Configuration Pills & Status */}
        <div className={styles.headerControls}>
          {/* Language Selector */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Globe size={14} color="var(--foreground-muted)" />
            <select
              className={styles.selectPill}
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              disabled={isConnected}
              title="Spoken Language Directives"
            >
              <option value="all">Code-Switching (All / Hinglish / Teluglish)</option>
              <option value="english">Indian English</option>
              <option value="hindi">Hindi</option>
              <option value="telugu">Telugu</option>
            </select>
          </div>

          {/* Status Badge */}
          <div
            className={`${styles.statusPill} ${
              connectionStatus === "agent-speaking" || connectionStatus === "tutor-speaking"
                ? styles.statusSpeaking
                : connectionStatus === "connected"
                ? styles.statusConnected
                : connectionStatus === "connecting"
                ? styles.statusConnecting
                : connectionStatus === "error"
                ? styles.statusError
                : styles.statusDisconnected
            }`}
          >
            {(connectionStatus === "agent-speaking" || connectionStatus === "tutor-speaking") && <Volume2 size={13} />}
            {connectionStatus === "connected" && <span className="pulse-indicator" style={{ background: "#39FF14" }} />}
            {connectionStatus === "connecting" && <span className="pulse-indicator" style={{ background: "#fbbf24" }} />}
            {connectionStatus === "error" && <AlertCircle size={13} />}
            <span style={{ textTransform: "capitalize" }}>
              {connectionStatus === "agent-speaking" || connectionStatus === "tutor-speaking"
                ? "Agent Speaking"
                : connectionStatus === "connected"
                ? "Agent Listening"
                : connectionStatus === "connecting"
                ? "Calling Prospect..."
                : "Idle"}
            </span>
          </div>

          {onClose && (
            <button onClick={onClose} className="btn btn-secondary btn-sm">
              Close
            </button>
          )}
        </div>
      </div>

      {/* Lead Call Sheet */}
      <LeadsSpreadsheetGrid
        activeLeadId={activeSpreadsheetLeadId}
        onSelectLead={handleSelectSpreadsheetLead}
        onBrowserMicCall={() => {
          if (!isConnected) startSession();
        }}
      />

      {/* Main Interactive Stage Grid */}
      <div className={styles.stageGrid}>
        {/* Left Pane: 3D Robot Visualizer and Audio Controls */}
        <div className={styles.visualizerPane}>
          <div className={styles.glowRing} />

          <div className={styles.visualizerCanvasWrapper}>
            <VoiceRobotVisualizer status={connectionStatus} isMuted={isMuted} />
          </div>

          {/* Live Status Message */}
          <div className={styles.statusMessageBar}>
            <span
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                background: isConnected ? "#39FF14" : "var(--foreground-muted)",
                display: "inline-block",
                flexShrink: 0,
              }}
            />
            <span style={{ fontSize: "12.5px" }}>{statusMessage}</span>
          </div>

          {/* Sentiment Badge */}
          {currentSentiment && isConnected && (
            <div className={styles.sentimentBadge}>
              <span>Client Mood:</span>
              <strong style={{ color: "var(--foreground)" }}>
                {currentSentiment.emoji} {currentSentiment.label}
              </strong>
            </div>
          )}

          {/* Controls Bar: Call/End Button + Mute + Clear */}
          <div className={styles.controlsBar}>
            {!isConnected ? (
              <button
                onClick={startSession}
                disabled={connectionStatus === "connecting"}
                className={`${styles.bigActionButton} ${styles.startBtn}`}
              >
                <PhoneCall size={18} />
                <span>{connectionStatus === "connecting" ? "DIALING..." : "CALL PROSPECT"}</span>
              </button>
            ) : (
              <>
                <button
                  onClick={endSession}
                  className={`${styles.bigActionButton} ${styles.endBtn}`}
                >
                  <PhoneOff size={18} />
                  <span>HANG UP</span>
                </button>

                <button
                  onClick={handleToggleMute}
                  className={`${styles.iconControlBtn} ${isMuted ? styles.iconControlBtnActive : ""}`}
                  title={isMuted ? "Unmute Microphone" : "Mute Microphone"}
                >
                  {isMuted ? <MicOff size={18} /> : <Mic size={18} />}
                </button>
              </>
            )}

            <button
              onClick={handleClearMessages}
              className={styles.iconControlBtn}
              title="Clear Transcript"
            >
              <RotateCcw size={18} />
            </button>
          </div>
        </div>

        {/* Right Pane: Live Chat Transcript Feed & Text Input */}
        <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
          <VoiceChatMessages
            messages={messages}
            isConnected={isConnected}
            status={connectionStatus}
          />

          {/* Text Input Fallback (User can type responses to test objections) */}
          <form onSubmit={handleSendText} className={styles.chatInputForm}>
            <input
              type="text"
              className={styles.chatInput}
              placeholder={
                isConnected
                  ? `Speak into mic or type client objection (e.g. "We don't need a website")...`
                  : "Click CALL PROSPECT to connect live voice call"
              }
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              disabled={!isConnected}
            />
            <button
              type="submit"
              disabled={!isConnected || !inputText.trim()}
              className={styles.chatSendBtn}
              title="Send Client Response"
            >
              <Send size={15} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
