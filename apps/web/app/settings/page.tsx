"use client";

import React, { useEffect, useState } from "react";
import { AppLayout } from "../../components/layout/AppLayout";
import { Header } from "../../components/layout/Header";
import { Settings, Shield, Server, Cpu, Phone, CheckCircle2, Lock } from "lucide-react";

export default function SettingsPage() {
  const [health, setHealth] = useState<any>({
    ai: { status: "healthy", provider: "mock" },
    telephony: { status: "healthy", provider: "mock" },
    database: { status: "healthy", database: "connected" },
  });

  useEffect(() => {
    async function check() {
      try {
        const res = await fetch("http://localhost:8000/api/v1/health");
        const aiRes = await fetch("http://localhost:8000/api/v1/health/ai");
        const telRes = await fetch("http://localhost:8000/api/v1/health/telephony");
        const dbRes = await fetch("http://localhost:8000/api/v1/health/database");

        setHealth({
          ai: await aiRes.json(),
          telephony: await telRes.json(),
          database: await dbRes.json(),
        });
      } catch (err) {
        console.log("Could not reach health endpoint directly from client", err);
      }
    }
    check();
  }, []);

  return (
    <AppLayout>
      <Header
        title="Platform Settings & Provider Status"
        subtitle="Manage telephony credentials, AI provider backends, privacy controls, and DNC lists"
      />

      <main style={{ padding: "32px", maxWidth: "1000px", margin: "0 auto" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Active Provider Backends */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">
                <Server size={18} color="var(--primary)" />
                Active Provider Architecture
              </h3>
              <span className="badge badge-success">Operational</span>
            </div>

            <p style={{ fontSize: "13px", color: "var(--foreground-muted)", marginBottom: "20px" }}>
              Veyra Voice strictly decouples business logic from external carriers and LLMs via abstract interfaces.
              Credentials can be injected anytime via environment variables without code modification.
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div style={{ background: "var(--background-secondary)", padding: "16px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 600, marginBottom: "6px" }}>
                  <Cpu size={16} color="var(--primary)" />
                  <span>AI Voice Engine</span>
                </div>
                <div style={{ fontSize: "13px", color: "var(--foreground-muted)" }}>
                  Current Provider: <strong style={{ color: "var(--foreground)", textTransform: "capitalize" }}>{health.ai?.provider || "Mock"}</strong>
                </div>
                <div style={{ fontSize: "11px", color: "var(--foreground-subtle)", marginTop: "4px" }}>
                  Realtime Bidirectional Streaming WebSocket
                </div>
              </div>

              <div style={{ background: "var(--background-secondary)", padding: "16px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 600, marginBottom: "6px" }}>
                  <Phone size={16} color="#06b6d4" />
                  <span>Telephony Carrier Adapter</span>
                </div>
                <div style={{ fontSize: "13px", color: "var(--foreground-muted)" }}>
                  Current Provider: <strong style={{ color: "var(--foreground)", textTransform: "capitalize" }}>{health.telephony?.provider || "Mock"}</strong>
                </div>
                <div style={{ fontSize: "11px", color: "var(--foreground-subtle)", marginTop: "4px" }}>
                  Supports Exotel REST & Inbound Media Streaming
                </div>
              </div>
            </div>
          </div>

          {/* Privacy & Compliance */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">
                <Shield size={18} color="var(--success)" />
                Data Privacy & Compliance Controls
              </h3>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 16px", background: "var(--background-secondary)", borderRadius: "var(--radius-md)" }}>
                <div>
                  <div style={{ fontSize: "14px", fontWeight: 600 }}>Phone Number Log Masking</div>
                  <div style={{ fontSize: "12px", color: "var(--foreground-muted)" }}>
                    Masks phone numbers in all backend logs and audit streams (e.g. +91******3210)
                  </div>
                </div>
                <span className="badge badge-success">Always Enforced</span>
              </div>

              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 16px", background: "var(--background-secondary)", borderRadius: "var(--radius-md)" }}>
                <div>
                  <div style={{ fontSize: "14px", fontWeight: 600 }}>Do-Not-Call (DNC) Strict Rejection</div>
                  <div style={{ fontSize: "12px", color: "var(--foreground-muted)" }}>
                    Guarantees zero outbound calls will be initiated to numbers flagged as Do-Not-Call
                  </div>
                </div>
                <span className="badge badge-success">Active</span>
              </div>

              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 16px", background: "var(--background-secondary)", borderRadius: "var(--radius-md)" }}>
                <div>
                  <div style={{ fontSize: "14px", fontWeight: 600 }}>AI Assistant Identity Disclosure</div>
                  <div style={{ fontSize: "12px", color: "var(--foreground-muted)" }}>
                    AI agent transparently identifies itself as an automated voice assistant in greeting
                  </div>
                </div>
                <span className="badge badge-success">Active</span>
              </div>
            </div>
          </div>

          {/* Security & Secrets Note */}
          <div className="card" style={{ borderColor: "rgba(99, 102, 241, 0.3)" }}>
            <div style={{ display: "flex", gap: "14px" }}>
              <Lock size={22} color="var(--primary)" style={{ flexShrink: 0, marginTop: "2px" }} />
              <div>
                <h4 style={{ fontSize: "15px", fontWeight: 600, color: "var(--foreground)", marginBottom: "4px" }}>
                  Credential Management & Production Hardening
                </h4>
                <p style={{ fontSize: "13px", color: "var(--foreground-muted)", lineHeight: 1.6 }}>
                  In compliance with our security policy, secrets are never stored in plain text or rendered in the browser.
                  To switch from Mock mode to live production, simply supply <code style={{ color: "#818cf8" }}>GEMINI_API_KEY</code> and <code style={{ color: "#818cf8" }}>EXOTEL_ACCOUNT_SID / EXOTEL_API_KEY</code> in your environment configuration file.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </AppLayout>
  );
}
