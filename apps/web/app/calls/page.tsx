"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { AppLayout } from "../../components/layout/AppLayout";
import { Header } from "../../components/layout/Header";
import { callsApi, campaignsApi } from "../../lib/api";
import { PhoneCall, ExternalLink, RefreshCw, Filter } from "lucide-react";

export default function CallsPage() {
  const [calls, setCalls] = useState<any[]>([]);
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [campaignFilter, setCampaignFilter] = useState<string>("");

  const loadCalls = async () => {
    setLoading(true);
    try {
      const [callsData, campsData] = await Promise.all([
        callsApi.list({
          status: statusFilter || undefined,
          campaign_id: campaignFilter || undefined,
        }),
        campaignsApi.list(),
      ]);
      setCalls(callsData);
      setCampaigns(campsData);
    } catch (err) {
      console.error("Failed to load calls", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCalls();
  }, [statusFilter, campaignFilter]);

  const getBadgeClass = (status: string) => {
    switch (status.toUpperCase()) {
      case "COMPLETED":
        return "badge-success";
      case "CONNECTED":
      case "IN_PROGRESS":
        return "badge-info";
      case "RINGING":
      case "INITIATING":
        return "badge-warning";
      case "FAILED":
      case "NO_ANSWER":
      case "BUSY":
        return "badge-danger";
      default:
        return "badge-neutral";
    }
  };

  return (
    <AppLayout>
      <Header
        title="Call History & Transcripts"
        subtitle="Review conversational voice sessions, AI turn-taking, and extracted answers"
        actions={
          <button onClick={loadCalls} className="btn btn-secondary btn-sm">
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
        }
      />

      <main style={{ padding: "32px", maxWidth: "1440px", margin: "0 auto" }}>
        {/* Filters */}
        <div className="card" style={{ marginBottom: "24px", padding: "16px 20px" }}>
          <div style={{ display: "flex", gap: "16px", flexWrap: "wrap", alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Filter size={16} color="var(--foreground-muted)" />
              <span style={{ fontSize: "13px", fontWeight: 500 }}>Filters:</span>
            </div>

            <select
              className="form-select"
              style={{ width: "220px" }}
              value={campaignFilter}
              onChange={(e) => setCampaignFilter(e.target.value)}
            >
              <option value="">All Campaigns</option>
              {campaigns.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>

            <select
              className="form-select"
              style={{ width: "180px" }}
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="COMPLETED">Completed</option>
              <option value="CONNECTED">Connected</option>
              <option value="RINGING">Ringing</option>
              <option value="NO_ANSWER">No Answer</option>
              <option value="BUSY">Busy</option>
              <option value="FAILED">Failed</option>
            </select>
          </div>
        </div>

        {/* Calls Table */}
        <div className="card">
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Contact Name</th>
                  <th>Phone Number</th>
                  <th>Status</th>
                  <th>Duration</th>
                  <th>Carrier Provider</th>
                  <th>Started At</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: "center", padding: "30px" }}>
                      Loading call logs...
                    </td>
                  </tr>
                ) : calls.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: "center", padding: "40px", color: "var(--foreground-muted)" }}>
                      No calls matching current criteria.
                    </td>
                  </tr>
                ) : (
                  calls.map((call) => (
                    <tr key={call.id}>
                      <td style={{ fontWeight: 600 }}>{call.lead?.full_name || "Unknown"}</td>
                      <td style={{ fontFamily: "var(--font-mono)", color: "var(--foreground)" }}>
                        {call.lead?.phone || "--"}
                      </td>
                      <td>
                        <span className={`badge ${getBadgeClass(call.status)}`}>
                          {call.status}
                        </span>
                      </td>
                      <td>{call.duration_seconds > 0 ? `${call.duration_seconds}s` : "--"}</td>
                      <td style={{ textTransform: "capitalize" }}>{call.provider}</td>
                      <td style={{ color: "var(--foreground-muted)", fontSize: "13px" }}>
                        {new Date(call.created_at).toLocaleString()}
                      </td>
                      <td>
                        <Link href={`/calls/${call.id}`} className="btn btn-secondary btn-sm" style={{ padding: "4px 10px" }}>
                          <span>Inspect</span>
                          <ExternalLink size={12} />
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </AppLayout>
  );
}
