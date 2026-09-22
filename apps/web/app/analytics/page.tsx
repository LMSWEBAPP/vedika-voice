"use client";

import React, { useEffect, useState } from "react";
import { AppLayout } from "../../components/layout/AppLayout";
import { Header } from "../../components/layout/Header";
import { CallsTrendChart } from "../../features/dashboard/components/CallsTrendChart";
import { OutcomesBreakdownChart } from "../../features/dashboard/components/OutcomesBreakdownChart";
import { analyticsApi } from "../../lib/api";
import { BarChart3, Globe, CheckCircle2, TrendingUp, Clock, RefreshCw } from "lucide-react";

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const data = await analyticsApi.getOverview();
      setOverview(data);
    } catch (err) {
      console.error("Failed to load analytics", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, []);

  const summary = overview?.summary || {};

  return (
    <AppLayout>
      <Header
        title="Voice Analytics & Intelligence"
        subtitle="Holistic performance reporting across campaigns, answer completion, and outcome distributions"
        actions={
          <button onClick={loadAnalytics} className="btn btn-secondary btn-sm">
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
        }
      />

      <main style={{ padding: "32px", maxWidth: "1440px", margin: "0 auto" }}>
        {/* KPI Strip */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "20px", marginBottom: "28px" }}>
          <div className="card" style={{ padding: "20px" }}>
            <div style={{ fontSize: "12px", color: "var(--foreground-muted)", textTransform: "uppercase" }}>Completion Rate</div>
            <div style={{ fontSize: "28px", fontWeight: 700, color: "var(--success)", marginTop: "6px" }}>
              {summary.completion_rate || 0}%
            </div>
            <div style={{ fontSize: "12px", color: "var(--foreground-subtle)", marginTop: "4px" }}>
              {summary.completed_calls || 0} of {summary.calls_made || 0} calls reached closing
            </div>
          </div>

          <div className="card" style={{ padding: "20px" }}>
            <div style={{ fontSize: "12px", color: "var(--foreground-muted)", textTransform: "uppercase" }}>Interest Rate</div>
            <div style={{ fontSize: "28px", fontWeight: 700, color: "#ec4899", marginTop: "6px" }}>
              {summary.conversion_rate || 0}%
            </div>
            <div style={{ fontSize: "12px", color: "var(--foreground-subtle)", marginTop: "4px" }}>
              {summary.interested_leads || 0} qualified affirmative leads
            </div>
          </div>

          <div className="card" style={{ padding: "20px" }}>
            <div style={{ fontSize: "12px", color: "var(--foreground-muted)", textTransform: "uppercase" }}>Average Call Duration</div>
            <div style={{ fontSize: "28px", fontWeight: 700, color: "#f59e0b", marginTop: "6px" }}>
              {Math.round(summary.average_duration_seconds || 0)}s
            </div>
            <div style={{ fontSize: "12px", color: "var(--foreground-subtle)", marginTop: "4px" }}>
              Avg duration per connected call
            </div>
          </div>

          <div className="card" style={{ padding: "20px" }}>
            <div style={{ fontSize: "12px", color: "var(--foreground-muted)", textTransform: "uppercase" }}>No Answer Rate</div>
            <div style={{ fontSize: "28px", fontWeight: 700, color: "#60a5fa", marginTop: "6px" }}>
              {summary.calls_made > 0 ? Math.round((summary.no_answer_calls / summary.calls_made) * 100) : 0}%
            </div>
            <div style={{ fontSize: "12px", color: "var(--foreground-subtle)", marginTop: "4px" }}>
              {summary.no_answer_calls || 0} unanswered contacts
            </div>
          </div>
        </div>

        {/* Charts Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "24px", marginBottom: "28px" }}>
          <CallsTrendChart data={overview?.calls_over_time || []} />
          <OutcomesBreakdownChart outcomes={overview?.outcomes || []} />
        </div>

        {/* Language Distribution Breakdown */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <Globe size={18} color="var(--accent-cyan)" />
              Multilingual Call Distribution
            </h3>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px" }}>
            {(overview?.languages || []).map((l: any) => (
              <div
                key={l.language}
                style={{
                  background: "var(--background-secondary)",
                  padding: "16px",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--border)",
                }}
              >
                <div style={{ fontSize: "13px", fontWeight: 600, textTransform: "uppercase", color: "var(--foreground)" }}>
                  {l.language === "en" ? "English" : l.language === "hi" ? "Hindi" : l.language === "te" ? "Telugu" : l.language}
                </div>
                <div style={{ fontSize: "22px", fontWeight: 700, color: "var(--primary)", marginTop: "4px" }}>
                  {l.count} calls
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </AppLayout>
  );
}
