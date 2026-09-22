"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { AppLayout } from "../../../components/layout/AppLayout";
import { Header } from "../../../components/layout/Header";
import { callsApi } from "../../../lib/api";
import { ArrowLeft, RotateCw, Bot, User, CheckCircle2, AlertTriangle, Clock, Layers } from "lucide-react";
import styles from "../../../styles/calls.module.css";

export default function CallDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [call, setCall] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [retrying, setRetrying] = useState(false);

  const loadDetails = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await callsApi.getDetails(id);
      setCall(data);
    } catch (err) {
      console.error("Failed to load call details", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDetails();
  }, [id]);

  const handleRetry = async () => {
    setRetrying(true);
    try {
      const newCall = await callsApi.retry(id);
      alert("Call retry scheduled!");
      router.push(`/calls/${newCall.id}`);
    } catch (err: any) {
      alert(err.message || "Failed to retry call");
    } finally {
      setRetrying(false);
    }
  };

  if (loading) {
    return (
      <AppLayout>
        <Header title="Call Inspection" />
        <main style={{ padding: "32px" }}>
          <div className="skeleton" style={{ height: "300px" }} />
        </main>
      </AppLayout>
    );
  }

  if (!call) {
    return (
      <AppLayout>
        <Header title="Call Not Found" />
        <main style={{ padding: "32px", textAlign: "center" }}>
          <p>Call record not found.</p>
          <Link href="/calls" className="btn btn-primary" style={{ marginTop: "16px" }}>
            Return to Calls
          </Link>
        </main>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <Header
        title={`Call with ${call.lead?.full_name || "Contact"}`}
        subtitle={`Session ID: ${call.id}`}
        actions={
          <div style={{ display: "flex", gap: "10px" }}>
            <Link href="/calls" className="btn btn-secondary btn-sm">
              <ArrowLeft size={14} />
              <span>Back</span>
            </Link>
            <button
              onClick={handleRetry}
              disabled={retrying}
              className="btn btn-primary btn-sm"
              title="Initiate follow-up call"
            >
              <RotateCw size={14} />
              <span>Retry Call</span>
            </button>
          </div>
        }
      />

      <main style={{ padding: "32px", maxWidth: "1440px", margin: "0 auto" }}>
        {/* Call Meta Banner */}
        <div className="card" style={{ marginBottom: "24px", padding: "18px 24px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "16px" }}>
            <div>
              <div style={{ fontSize: "12px", color: "var(--foreground-muted)", textTransform: "uppercase" }}>Phone Number</div>
              <div style={{ fontSize: "15px", fontWeight: 600, fontFamily: "var(--font-mono)", marginTop: "4px" }}>
                {call.lead?.phone || "N/A"}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "12px", color: "var(--foreground-muted)", textTransform: "uppercase" }}>Company</div>
              <div style={{ fontSize: "15px", fontWeight: 600, marginTop: "4px" }}>{call.lead?.company || "--"}</div>
            </div>
            <div>
              <div style={{ fontSize: "12px", color: "var(--foreground-muted)", textTransform: "uppercase" }}>Status</div>
              <div style={{ marginTop: "4px" }}>
                <span className={`badge ${call.status === "COMPLETED" ? "badge-success" : "badge-info"}`}>
                  {call.status}
                </span>
              </div>
            </div>
            <div>
              <div style={{ fontSize: "12px", color: "var(--foreground-muted)", textTransform: "uppercase" }}>Duration</div>
              <div style={{ fontSize: "15px", fontWeight: 600, marginTop: "4px" }}>
                {call.duration_seconds > 0 ? `${call.duration_seconds} seconds` : "--"}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "12px", color: "var(--foreground-muted)", textTransform: "uppercase" }}>Provider Call ID</div>
              <div style={{ fontSize: "13px", color: "var(--foreground-muted)", fontFamily: "var(--font-mono)", marginTop: "4px" }}>
                {call.provider_call_id || "N/A"}
              </div>
            </div>
          </div>
        </div>

        {/* Two Column Inspection Canvas: Transcript on Left, Extracted Answers on Right */}
        <div style={{ display: "grid", gridTemplateColumns: "3fr 2fr", gap: "24px", alignItems: "start" }}>
          {/* Column 1: Transcript */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">
                <Bot size={18} color="var(--primary)" />
                Live Conversation Transcript
              </h3>
              <span style={{ fontSize: "12px", color: "var(--foreground-muted)" }}>
                {call.transcripts?.length || 0} Turns Recorded
              </span>
            </div>

            <div className={styles.transcriptContainer}>
              {(!call.transcripts || call.transcripts.length === 0) ? (
                <div style={{ textAlign: "center", padding: "40px", color: "var(--foreground-muted)" }}>
                  No transcript turns recorded for this call session.
                </div>
              ) : (
                call.transcripts.map((turn: any) => {
                  const isAi = turn.speaker.toLowerCase() === "ai";
                  return (
                    <div
                      key={turn.id}
                      className={`${styles.turnBubble} ${isAi ? styles.aiBubble : styles.userBubble}`}
                    >
                      <div className={`${styles.bubbleSpeaker} ${isAi ? styles.aiSpeaker : styles.userSpeaker}`}>
                        {isAi ? <Bot size={14} /> : <User size={14} />}
                        <span>{isAi ? "AI Voice Agent" : (call.lead?.full_name || "Customer")}</span>
                      </div>
                      <div>{turn.text}</div>
                      <div className={styles.bubbleTime}>
                        {new Date(turn.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Column 2: Structured Extracted Answers & Event Log */}
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            {/* Structured Answers */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">
                  <CheckCircle2 size={18} color="var(--success)" />
                  Extracted Structured Answers
                </h3>
              </div>

              {(!call.answers || call.answers.length === 0) ? (
                <p style={{ color: "var(--foreground-muted)", fontSize: "13px" }}>
                  No answers extracted yet. Answers appear automatically upon call completion.
                </p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  {call.answers.map((ans: any) => (
                    <div key={ans.id} className={styles.answerCard}>
                      <div className={styles.answerQuestion}>{ans.question_text}</div>
                      <div className={styles.answerValue}>
                        {typeof ans.extracted_value === "boolean"
                          ? ans.extracted_value ? "Yes (Confirmed)" : "No"
                          : String(ans.extracted_value || ans.raw_answer)}
                      </div>
                      <div className={styles.answerMeta}>
                        <span className={`badge ${ans.is_valid ? "badge-success" : "badge-warning"}`}>
                          {ans.is_valid ? "Valid" : "Uncertain"}
                        </span>
                        <span style={{ color: "var(--foreground-subtle)" }}>
                          Confidence: {Math.round(ans.confidence * 100)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Event Audit Log */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">
                  <Layers size={18} color="#06b6d4" />
                  Call Lifecycle State Events
                </h3>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {(call.events || []).map((ev: any) => (
                  <div
                    key={ev.id}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      fontSize: "12px",
                      padding: "8px 12px",
                      background: "rgba(255,255,255,0.02)",
                      borderRadius: "var(--radius-sm)",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    <span style={{ fontWeight: 600, color: "var(--foreground)" }}>{ev.event_type}</span>
                    <span style={{ color: "var(--foreground-muted)" }}>
                      {new Date(ev.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </AppLayout>
  );
}
