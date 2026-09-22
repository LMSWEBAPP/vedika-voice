"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { AppLayout } from "../../../components/layout/AppLayout";
import { Header } from "../../../components/layout/Header";
import { campaignsApi, leadsApi, callsApi } from "../../../lib/api";
import { Play, Pause, Square, Bot, ArrowLeft, Users, PhoneCall, CheckCircle } from "lucide-react";

export default function CampaignDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [campaign, setCampaign] = useState<any>(null);
  const [leads, setLeads] = useState<any[]>([]);
  const [calls, setCalls] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"script" | "leads" | "calls">("script");

  const loadAll = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [campData, leadsData, callsData] = await Promise.all([
        campaignsApi.get(id),
        leadsApi.getCampaignLeads(id),
        callsApi.list({ campaign_id: id }),
      ]);
      setCampaign(campData);
      setLeads(leadsData);
      setCalls(callsData);
    } catch (err) {
      console.error("Failed to load campaign details", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, [id]);

  const handleStatus = async (action: "start" | "pause" | "stop") => {
    try {
      if (action === "start") await campaignsApi.start(id);
      else if (action === "pause") await campaignsApi.pause(id);
      else if (action === "stop") await campaignsApi.stop(id);
      loadAll();
    } catch (err: any) {
      alert(err.message || "Failed to update campaign");
    }
  };

  if (loading) {
    return (
      <AppLayout>
        <Header title="Campaign Details" />
        <main style={{ padding: "32px" }}>
          <div className="skeleton" style={{ height: "300px" }} />
        </main>
      </AppLayout>
    );
  }

  if (!campaign) {
    return (
      <AppLayout>
        <Header title="Campaign Not Found" />
        <main style={{ padding: "32px", textAlign: "center" }}>
          <p>The requested campaign could not be found.</p>
          <Link href="/campaigns" className="btn btn-primary" style={{ marginTop: "16px" }}>
            Return to Campaigns
          </Link>
        </main>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <Header
        title={campaign.name}
        subtitle={campaign.objective}
        actions={
          <div style={{ display: "flex", gap: "10px" }}>
            <Link href="/campaigns" className="btn btn-secondary btn-sm">
              <ArrowLeft size={14} />
              <span>Back</span>
            </Link>
            {campaign.status !== "ACTIVE" ? (
              <button onClick={() => handleStatus("start")} className="btn btn-primary btn-sm">
                <Play size={14} />
                <span>Start Calling</span>
              </button>
            ) : (
              <button onClick={() => handleStatus("pause")} className="btn btn-secondary btn-sm">
                <Pause size={14} />
                <span>Pause</span>
              </button>
            )}
            {campaign.status === "ACTIVE" && (
              <button onClick={() => handleStatus("stop")} className="btn btn-danger btn-sm">
                <Square size={14} />
                <span>Stop</span>
              </button>
            )}
            <Link href={`/agent-builder?campaignId=${campaign.id}`} className="btn btn-secondary btn-sm">
              <Bot size={14} color="var(--primary)" />
              <span>Edit Script & Test Mic</span>
            </Link>
          </div>
        }
      />

      <main style={{ padding: "32px", maxWidth: "1440px", margin: "0 auto" }}>
        {/* Metric Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px", marginBottom: "28px" }}>
          <div className="card" style={{ padding: "16px 20px" }}>
            <div style={{ fontSize: "12px", color: "var(--foreground-muted)", textTransform: "uppercase" }}>Status</div>
            <div style={{ fontSize: "20px", fontWeight: 700, marginTop: "4px" }}>
              <span className={`badge ${campaign.status === "ACTIVE" ? "badge-success" : "badge-neutral"}`}>
                {campaign.status}
              </span>
            </div>
          </div>
          <div className="card" style={{ padding: "16px 20px" }}>
            <div style={{ fontSize: "12px", color: "var(--foreground-muted)", textTransform: "uppercase" }}>Leads</div>
            <div style={{ fontSize: "24px", fontWeight: 700, marginTop: "4px" }}>{leads.length}</div>
          </div>
          <div className="card" style={{ padding: "16px 20px" }}>
            <div style={{ fontSize: "12px", color: "var(--foreground-muted)", textTransform: "uppercase" }}>Calls Completed</div>
            <div style={{ fontSize: "24px", fontWeight: 700, marginTop: "4px" }}>
              {calls.filter((c) => c.status === "COMPLETED").length}
            </div>
          </div>
          <div className="card" style={{ padding: "16px 20px" }}>
            <div style={{ fontSize: "12px", color: "var(--foreground-muted)", textTransform: "uppercase" }}>Language</div>
            <div style={{ fontSize: "20px", fontWeight: 700, marginTop: "4px", textTransform: "uppercase" }}>
              {campaign.primary_language}
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid var(--border)", marginBottom: "24px" }}>
          <button
            onClick={() => setActiveTab("script")}
            className={`btn ${activeTab === "script" ? "btn-primary" : "btn-secondary"}`}
            style={{ borderRadius: "var(--radius-md) var(--radius-md) 0 0" }}
          >
            Script & Questions
          </button>
          <button
            onClick={() => setActiveTab("leads")}
            className={`btn ${activeTab === "leads" ? "btn-primary" : "btn-secondary"}`}
            style={{ borderRadius: "var(--radius-md) var(--radius-md) 0 0" }}
          >
            Assigned Leads ({leads.length})
          </button>
          <button
            onClick={() => setActiveTab("calls")}
            className={`btn ${activeTab === "calls" ? "btn-primary" : "btn-secondary"}`}
            style={{ borderRadius: "var(--radius-md) var(--radius-md) 0 0" }}
          >
            Call History ({calls.length})
          </button>
        </div>

        {/* Tab 1: Script */}
        {activeTab === "script" && (
          <div className="card animate-fade-in">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
              <h3 className="card-title">Structured Voice Agent Script</h3>
              <Link href={`/agent-builder?campaignId=${campaign.id}`} className="btn btn-primary btn-sm">
                Open in Agent Builder
              </Link>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div style={{ background: "rgba(255,255,255,0.02)", padding: "14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
                <span style={{ fontSize: "12px", color: "var(--foreground-muted)", textTransform: "uppercase", fontWeight: 600 }}>Opening Greeting</span>
                <p style={{ marginTop: "4px", fontSize: "15px", color: "var(--foreground)" }}>{campaign.script?.opening || "None"}</p>
              </div>

              <div>
                <span style={{ fontSize: "12px", color: "var(--foreground-muted)", textTransform: "uppercase", fontWeight: 600 }}>Questions & Extraction Logic</span>
                <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "8px" }}>
                  {(campaign.script?.questions || []).map((q: any, i: number) => (
                    <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", background: "var(--background-secondary)", padding: "12px 16px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)" }}>
                      <div>
                        <div style={{ fontSize: "14px", fontWeight: 500 }}>{q.text}</div>
                        {q.condition && (
                          <div style={{ fontSize: "12px", color: "#818cf8", marginTop: "4px" }}>
                            Branch condition: if {q.condition.depends_on_question_id} {q.condition.operator} {String(q.condition.expected_value)}
                          </div>
                        )}
                      </div>
                      <span className="badge badge-info">{q.type}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ background: "rgba(255,255,255,0.02)", padding: "14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
                <span style={{ fontSize: "12px", color: "var(--foreground-muted)", textTransform: "uppercase", fontWeight: 600 }}>Closing Statement</span>
                <p style={{ marginTop: "4px", fontSize: "15px", color: "var(--foreground)" }}>{campaign.script?.closing || "None"}</p>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Leads */}
        {activeTab === "leads" && (
          <div className="card animate-fade-in">
            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Lead Name</th>
                    <th>Phone</th>
                    <th>Status</th>
                    <th>Attempts</th>
                    <th>Last Called</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.length === 0 ? (
                    <tr>
                      <td colSpan={5} style={{ textAlign: "center", padding: "30px", color: "var(--foreground-muted)" }}>
                        No leads assigned to this campaign yet.
                      </td>
                    </tr>
                  ) : (
                    leads.map((cl: any) => (
                      <tr key={cl.id}>
                        <td style={{ fontWeight: 600 }}>{cl.lead?.full_name || "Unknown"}</td>
                        <td style={{ fontFamily: "var(--font-mono)", color: "var(--foreground-muted)" }}>{cl.lead?.phone}</td>
                        <td>
                          <span className={`badge ${cl.status === "INTERESTED" ? "badge-success" : cl.status === "DO_NOT_CALL" ? "badge-danger" : "badge-neutral"}`}>
                            {cl.status}
                          </span>
                        </td>
                        <td>{cl.attempts}</td>
                        <td>{cl.last_called_at ? new Date(cl.last_called_at).toLocaleString() : "Never"}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: Calls */}
        {activeTab === "calls" && (
          <div className="card animate-fade-in">
            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Contact</th>
                    <th>Phone</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Timestamp</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {calls.length === 0 ? (
                    <tr>
                      <td colSpan={6} style={{ textAlign: "center", padding: "30px", color: "var(--foreground-muted)" }}>
                        No calls placed for this campaign yet.
                      </td>
                    </tr>
                  ) : (
                    calls.map((call: any) => (
                      <tr key={call.id}>
                        <td style={{ fontWeight: 600 }}>{call.lead?.full_name || "Unknown"}</td>
                        <td style={{ fontFamily: "var(--font-mono)", color: "var(--foreground-muted)" }}>{call.lead?.phone}</td>
                        <td>
                          <span className="badge badge-info">{call.status}</span>
                        </td>
                        <td>{call.duration_seconds > 0 ? `${call.duration_seconds}s` : "--"}</td>
                        <td>{new Date(call.created_at).toLocaleString()}</td>
                        <td>
                          <Link href={`/calls/${call.id}`} className="btn btn-secondary btn-sm">
                            Inspect
                          </Link>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </AppLayout>
  );
}
