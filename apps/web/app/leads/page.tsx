"use client";

import React, { useEffect, useState } from "react";
import { AppLayout } from "../../components/layout/AppLayout";
import { Header } from "../../components/layout/Header";
import { CsvUploadModal } from "../../features/leads/components/CsvUploadModal";
import { CreateLeadModal } from "../../features/leads/components/CreateLeadModal";
import { leadsApi, campaignsApi, callsApi } from "../../lib/api";
import { Plus, Upload, Search, PhoneCall, ShieldAlert, ShieldCheck, Check, User } from "lucide-react";

export default function LeadsPage() {
  const [leads, setLeads] = useState<any[]>([]);
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [dncFilter, setDncFilter] = useState<boolean | undefined>(undefined);
  const [csvOpen, setCsvOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState<string>("");
  const [callingLeadId, setCallingLeadId] = useState<string | null>(null);

  const loadLeads = async () => {
    setLoading(true);
    try {
      const [leadsData, campsData] = await Promise.all([
        leadsApi.list({ search: search || undefined, do_not_call: dncFilter }),
        campaignsApi.list(),
      ]);
      setLeads(leadsData);
      setCampaigns(campsData);
      if (campsData.length > 0 && !selectedCampaign) {
        setSelectedCampaign(campsData[0].id);
      }
    } catch (err) {
      console.error("Failed to load leads", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLeads();
  }, [dncFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadLeads();
  };

  const handleToggleDnc = async (lead: any) => {
    try {
      await leadsApi.toggleDNC(lead.id, !lead.do_not_call);
      loadLeads();
    } catch (err: any) {
      alert(err.message || "Failed to update DNC status");
    }
  };

  const handleInitiateCall = async (leadId: string) => {
    if (!selectedCampaign) {
      alert("Please select a campaign first to initiate a call.");
      return;
    }
    setCallingLeadId(leadId);
    try {
      await callsApi.initiate(selectedCampaign, leadId);
      alert("Call initiated successfully! Transitioning to live status.");
    } catch (err: any) {
      alert(err.message || "Failed to initiate call");
    } finally {
      setCallingLeadId(null);
    }
  };

  return (
    <AppLayout>
      <Header
        title="Lead Management"
        subtitle="Manage customer contact lists, upload CSV datasets, and enforce Do-Not-Call compliance"
        actions={
          <div style={{ display: "flex", gap: "10px" }}>
            <button onClick={() => setCsvOpen(true)} className="btn btn-secondary btn-sm">
              <Upload size={14} />
              <span>Import CSV</span>
            </button>
            <button onClick={() => setCreateOpen(true)} className="btn btn-primary btn-sm">
              <Plus size={14} />
              <span>Add Lead</span>
            </button>
          </div>
        }
      />

      <main style={{ padding: "32px", maxWidth: "1440px", margin: "0 auto" }}>
        {/* Search & Filter Bar */}
        <div className="card" style={{ marginBottom: "24px", padding: "16px 20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "16px", alignItems: "center" }}>
            <form onSubmit={handleSearchSubmit} style={{ display: "flex", gap: "10px", flex: "1", minWidth: "260px" }}>
              <div style={{ position: "relative", width: "100%" }}>
                <Search size={16} style={{ position: "absolute", left: "12px", top: "12px", color: "var(--foreground-muted)" }} />
                <input
                  type="text"
                  className="form-input"
                  placeholder="Search by name, phone, email, or company..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  style={{ paddingLeft: "36px", width: "100%" }}
                />
              </div>
              <button type="submit" className="btn btn-secondary">
                Search
              </button>
            </form>

            <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
              <label style={{ fontSize: "13px", color: "var(--foreground-muted)" }}>Target Campaign:</label>
              <select
                className="form-select"
                style={{ width: "200px" }}
                value={selectedCampaign}
                onChange={(e) => setSelectedCampaign(e.target.value)}
              >
                {campaigns.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>

              <button
                onClick={() => setDncFilter(dncFilter === undefined ? true : dncFilter ? false : undefined)}
                className={`btn btn-sm ${dncFilter !== undefined ? "btn-primary" : "btn-secondary"}`}
              >
                {dncFilter === undefined ? "All Statuses" : dncFilter ? "DNC Only" : "Callable Only"}
              </button>
            </div>
          </div>
        </div>

        {/* Leads Table */}
        <div className="card">
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Contact</th>
                  <th>Phone Number</th>
                  <th>Company</th>
                  <th>Email</th>
                  <th>DNC Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: "center", padding: "30px" }}>
                      Loading leads...
                    </td>
                  </tr>
                ) : leads.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: "center", padding: "40px", color: "var(--foreground-muted)" }}>
                      No leads found. Import a CSV file or add individual leads to begin.
                    </td>
                  </tr>
                ) : (
                  leads.map((lead) => (
                    <tr key={lead.id}>
                      <td style={{ fontWeight: 600, color: "var(--foreground)" }}>
                        {lead.full_name || "Unknown"}
                      </td>
                      <td style={{ fontFamily: "var(--font-mono)", color: "var(--foreground)" }}>
                        {lead.phone}
                      </td>
                      <td>{lead.company || "--"}</td>
                      <td style={{ color: "var(--foreground-muted)", fontSize: "13px" }}>{lead.email || "--"}</td>
                      <td>
                        {lead.do_not_call ? (
                          <span className="badge badge-danger">DNC Blocked</span>
                        ) : (
                          <span className="badge badge-success">Callable</span>
                        )}
                      </td>
                      <td style={{ color: "var(--foreground-muted)", fontSize: "12px" }}>
                        {new Date(lead.created_at).toLocaleDateString()}
                      </td>
                      <td>
                        <div style={{ display: "flex", gap: "6px" }}>
                          <button
                            onClick={() => handleInitiateCall(lead.id)}
                            disabled={lead.do_not_call || callingLeadId === lead.id}
                            className="btn btn-primary btn-sm"
                            title={lead.do_not_call ? "Cannot call DNC contact" : "Call with AI"}
                          >
                            <PhoneCall size={12} />
                            <span>Call</span>
                          </button>
                          <button
                            onClick={() => handleToggleDnc(lead)}
                            className="btn btn-secondary btn-sm"
                            title="Toggle Do Not Call"
                          >
                            {lead.do_not_call ? <ShieldCheck size={12} color="var(--success)" /> : <ShieldAlert size={12} color="var(--danger)" />}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <CsvUploadModal
          isOpen={csvOpen}
          onClose={() => setCsvOpen(false)}
          onSuccess={loadLeads}
          campaigns={campaigns}
        />

        <CreateLeadModal
          isOpen={createOpen}
          onClose={() => setCreateOpen(false)}
          onCreated={loadLeads}
        />
      </main>
    </AppLayout>
  );
}
