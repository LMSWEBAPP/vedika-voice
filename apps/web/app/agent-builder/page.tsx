"use client";

import React, { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AppLayout } from "../../components/layout/AppLayout";
import { Header } from "../../components/layout/Header";
import { LiveVoiceTester } from "../../features/agent/components/LiveVoiceTester";
import { campaignsApi, agentsApi } from "../../lib/api";
import { Bot, Plus, Trash2, Save, Sparkles, CheckCircle2 } from "lucide-react";
import styles from "../../styles/agent.module.css";

function AgentBuilderContent() {
  const searchParams = useSearchParams();
  const initialCampaignId = searchParams.get("campaignId") || "";

  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState<string>(initialCampaignId);
  const [voices, setVoices] = useState<any[]>([]);
  const [questionTypes, setQuestionTypes] = useState<any[]>([]);

  // Script State
  const [persona, setPersona] = useState("Courteous, consultative, and concise executive representative.");
  const [voiceName, setVoiceName] = useState("Aoede");
  const [opening, setOpening] = useState("Hello! Thank you for taking my call.");
  const [objective, setObjective] = useState("Qualify lead interest and team requirements.");
  const [closing, setClosing] = useState("Thank you very much for your time today. Goodbye!");
  const [questions, setQuestions] = useState<any[]>([
    { id: "q1_interest", text: "Are you interested in automating your outbound calls?", type: "boolean", required: true },
    { id: "q2_team_size", text: "How many representatives are on your team?", type: "number", required: false },
  ]);

  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    async function init() {
      try {
        const [campsData, voicesData, typesData] = await Promise.all([
          campaignsApi.list(),
          agentsApi.getVoices(),
          agentsApi.getQuestionTypes(),
        ]);
        setCampaigns(campsData);
        setVoices(voicesData);
        setQuestionTypes(typesData);

        const targetId = initialCampaignId || (campsData[0]?.id ?? "");
        if (targetId) {
          setSelectedCampaignId(targetId);
          loadCampaignScript(targetId);
        }
      } catch (err) {
        console.error("Init error in Agent Builder", err);
      }
    }
    init();
  }, [initialCampaignId]);

  const loadCampaignScript = async (campId: string) => {
    try {
      const camp = await campaignsApi.get(campId);
      if (camp.script) {
        setPersona(camp.script.persona || "");
        setVoiceName(camp.script.voice_name || "Aoede");
        setOpening(camp.script.opening || "");
        setObjective(camp.script.objective || "");
        setClosing(camp.script.closing || "");
        if (camp.script.questions?.length > 0) {
          setQuestions(camp.script.questions);
        }
      }
    } catch (err) {
      console.error("Failed to load script", err);
    }
  };

  const handleCampaignSelect = (campId: string) => {
    setSelectedCampaignId(campId);
    loadCampaignScript(campId);
  };

  const addQuestion = () => {
    const newId = `q${questions.length + 1}_${Date.now().toString().slice(-4)}`;
    setQuestions([
      ...questions,
      { id: newId, text: "New qualification question?", type: "text", required: true },
    ]);
  };

  const removeQuestion = (idx: number) => {
    setQuestions(questions.filter((_, i) => i !== idx));
  };

  const updateQuestion = (idx: number, field: string, value: any) => {
    const updated = [...questions];
    updated[idx] = { ...updated[idx], [field]: value };
    setQuestions(updated);
  };

  const handleSave = async () => {
    if (!selectedCampaignId) {
      alert("Please select a campaign to attach this script to.");
      return;
    }
    setSaving(true);
    setSavedSuccess(false);
    try {
      await campaignsApi.updateScript(selectedCampaignId, {
        persona,
        voice_name: voiceName,
        opening,
        objective,
        questions,
        closing,
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err: any) {
      alert(err.message || "Failed to save script");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppLayout>
      <Header
        title="Agent Configuration & Live Voice Studio"
        subtitle="Shape your conversational agent's personality, structured questions, and test in real-time"
        actions={
          <button onClick={handleSave} disabled={saving} className="btn btn-primary btn-sm">
            <Save size={14} />
            <span>{saving ? "Saving..." : savedSuccess ? "Saved Successfully!" : "Save Script"}</span>
          </button>
        }
      />

      <main style={{ padding: "32px", maxWidth: "1440px", margin: "0 auto" }}>
        {/* Campaign Selector Banner */}
        <div className="card" style={{ marginBottom: "24px", padding: "16px 20px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <Bot size={18} color="var(--primary)" />
              <span style={{ fontSize: "14px", fontWeight: 600 }}>Active Campaign Target:</span>
              <select
                className="form-select"
                value={selectedCampaignId}
                onChange={(e) => handleCampaignSelect(e.target.value)}
                style={{ minWidth: "260px" }}
              >
                {campaigns.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.status})
                  </option>
                ))}
              </select>
            </div>

            {savedSuccess && (
              <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--success)", fontSize: "13px" }}>
                <CheckCircle2 size={16} />
                <span>Script updated on server! Ready for live testing.</span>
              </div>
            )}
          </div>
        </div>

        {/* Studio Grid: Script Configuration on Left, Live Tester on Right */}
        <div className={styles.agentBuilderGrid}>
          {/* Left Column: Script Editor */}
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            {/* Persona & Voice Selection */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Personality & Voice Profile</h3>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                <div className="form-group">
                  <label className="form-label">Voice Synthesis Profile</label>
                  <select
                    className="form-select"
                    value={voiceName}
                    onChange={(e) => setVoiceName(e.target.value)}
                  >
                    {voices.map((v) => (
                      <option key={v.name} value={v.name}>
                        {v.name} ({v.gender} - {v.style})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Conversation Objective</label>
                  <input
                    type="text"
                    className="form-input"
                    value={objective}
                    onChange={(e) => setObjective(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Agent Persona & Tone Directives</label>
                <textarea
                  className="form-textarea"
                  rows={2}
                  value={persona}
                  onChange={(e) => setPersona(e.target.value)}
                />
              </div>
            </div>

            {/* Conversation Flow */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Opening & Sign-off</h3>
              </div>

              <div className="form-group">
                <label className="form-label">Opening Greeting Line *</label>
                <textarea
                  className="form-textarea"
                  rows={2}
                  value={opening}
                  onChange={(e) => setOpening(e.target.value)}
                />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Closing Sign-off *</label>
                <textarea
                  className="form-textarea"
                  rows={2}
                  value={closing}
                  onChange={(e) => setClosing(e.target.value)}
                />
              </div>
            </div>

            {/* Structured Questions */}
            <div className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Required Questions & Structured Extraction</h3>
                  <p style={{ fontSize: "12px", color: "var(--foreground-muted)", marginTop: "2px" }}>
                    The AI agent dynamically steers dialogue to elicit these fields without reading rigidly.
                  </p>
                </div>
                <button onClick={addQuestion} className="btn btn-secondary btn-sm">
                  <Plus size={14} />
                  <span>Add Question</span>
                </button>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {questions.map((q, idx) => (
                  <div key={idx} className={styles.questionItem}>
                    <div className={styles.questionHeader}>
                      <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--primary)" }}>
                        #{idx + 1} ID: {q.id}
                      </span>
                      <button
                        onClick={() => removeQuestion(idx)}
                        className="btn-icon"
                        style={{ color: "var(--danger)" }}
                        title="Remove Question"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "3fr 1fr", gap: "12px" }}>
                      <input
                        type="text"
                        className="form-input"
                        placeholder="Question spoken by the AI..."
                        value={q.text}
                        onChange={(e) => updateQuestion(idx, "text", e.target.value)}
                      />

                      <select
                        className="form-select"
                        value={q.type}
                        onChange={(e) => updateQuestion(idx, "type", e.target.value)}
                      >
                        {questionTypes.map((t) => (
                          <option key={t.type} value={t.type}>
                            {t.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "16px", fontSize: "12px" }}>
                      <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
                        <input
                          type="checkbox"
                          checked={q.required}
                          onChange={(e) => updateQuestion(idx, "required", e.target.checked)}
                          style={{ accentColor: "var(--primary)" }}
                        />
                        <span>Required Field</span>
                      </label>

                      {idx > 0 && (
                        <div className={styles.conditionBox}>
                          Conditional Branch: asks only if #{idx} was affirmed or answered
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: In-Browser Live Tester */}
          <div>
            <LiveVoiceTester
              campaignId={selectedCampaignId}
              script={{
                persona,
                voice_name: voiceName,
                opening,
                objective,
                questions,
                closing,
              }}
            />
          </div>
        </div>
      </main>
    </AppLayout>
  );
}

export default function AgentBuilderPage() {
  return (
    <Suspense
      fallback={
        <AppLayout>
          <Header title="Agent Configuration & Live Voice Studio" />
          <main style={{ padding: "32px" }}>
            <div className="skeleton" style={{ height: "300px" }} />
          </main>
        </AppLayout>
      }
    >
      <AgentBuilderContent />
    </Suspense>
  );
}
