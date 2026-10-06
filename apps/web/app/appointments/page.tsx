"use client";

import React, { useEffect, useState } from "react";
import { AppLayout } from "../../components/layout/AppLayout";
import { Header } from "../../components/layout/Header";
import { appointmentsApi } from "../../lib/api";
import {
  Calendar,
  Clock,
  MessageSquare,
  Phone,
  Video,
  CheckCircle2,
  Bell,
  RefreshCw,
  Building,
  User,
} from "lucide-react";

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");

  const loadAppointments = async () => {
    setLoading(true);
    try {
      const data = await appointmentsApi.list({ status: statusFilter || undefined });
      setAppointments(data);
    } catch (err) {
      console.error("Failed to load appointments", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAppointments();
  }, [statusFilter]);

  const handleMarkReminderSent = async (id: string) => {
    try {
      await appointmentsApi.markReminderSent(id);
      loadAppointments();
    } catch (err: any) {
      alert(err.message || "Failed to mark reminder sent");
    }
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case "WhatsApp":
        return <MessageSquare size={14} color="#25D366" />;
      case "Google Meet":
        return <Video size={14} color="#3b82f6" />;
      default:
        return <Phone size={14} color="var(--primary)" />;
    }
  };

  const getStatusBadge = (status: string, reminderSent: boolean) => {
    if (status === "COMPLETED") return <span className="badge badge-success">Completed</span>;
    if (status === "CONFIRMED") return <span className="badge badge-info">Confirmed</span>;
    if (reminderSent) return <span className="badge badge-info">Reminder Sent</span>;
    return <span className="badge badge-warning">Reminder Scheduled</span>;
  };

  return (
    <AppLayout>
      <Header
        title="Booked Appointments & Demo Reminders"
        subtitle="Meetings secured by Madhu for custom software, web app, and automation demos"
        actions={
          <button onClick={loadAppointments} className="btn btn-secondary btn-sm">
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
        }
      />

      <main style={{ padding: "32px", maxWidth: "1440px", margin: "0 auto" }}>
        {/* Filter Bar */}
        <div className="card" style={{ marginBottom: "24px", padding: "16px 20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <Calendar size={18} color="var(--primary)" />
              <span style={{ fontSize: "14px", fontWeight: 600 }}>Filter by Status:</span>
              <select
                className="form-select"
                style={{ width: "220px" }}
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All Bookings</option>
                <option value="REMINDER_SCHEDULED">Reminder Scheduled</option>
                <option value="CONFIRMED">Confirmed</option>
                <option value="COMPLETED">Completed</option>
              </select>
            </div>

            <div style={{ fontSize: "13px", color: "var(--foreground-muted)" }}>
              Total Demos Booked: <strong style={{ color: "var(--foreground)" }}>{appointments.length}</strong>
            </div>
          </div>
        </div>

        {/* Appointments Table */}
        <div className="card">
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Client / Company</th>
                  <th>Domain / Need</th>
                  <th>Scheduled Date & Time</th>
                  <th>Channel</th>
                  <th>Status & Reminder</th>
                  <th>Software Requirement Notes</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: "center", padding: "30px" }}>
                      Loading scheduled appointments...
                    </td>
                  </tr>
                ) : appointments.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: "center", padding: "40px", color: "var(--foreground-muted)" }}>
                      No demo appointments recorded yet. When Madhu finishes an affirmative cold call, booked slots appear here automatically!
                    </td>
                  </tr>
                ) : (
                  appointments.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <div style={{ fontWeight: 600, color: "var(--foreground)" }}>
                          {item.lead?.full_name || "Prospect"}
                        </div>
                        <div style={{ fontSize: "12px", color: "var(--foreground-muted)" }}>
                          {item.lead?.company || "Independent"} · {item.lead?.phone}
                        </div>
                      </td>
                      <td>
                        <span className="badge badge-neutral" style={{ textTransform: "none", fontSize: "11px" }}>
                          {item.lead?.custom_data?.domain || "Custom Software"}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontWeight: 500 }}>
                          <Clock size={13} color="var(--primary)" />
                          <span>{new Date(item.scheduled_at).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })}</span>
                        </div>
                      </td>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "13px" }}>
                          {getChannelIcon(item.contact_channel)}
                          <span>{item.contact_channel}</span>
                        </div>
                      </td>
                      <td>
                        {getStatusBadge(item.status, item.reminder_sent)}
                      </td>
                      <td style={{ maxWidth: "300px", fontSize: "12px", color: "var(--foreground-muted)", lineHeight: 1.4 }}>
                        {item.requirement_notes || "General 15-minute custom software exploration."}
                      </td>
                      <td>
                        {!item.reminder_sent && item.status !== "COMPLETED" ? (
                          <button
                            onClick={() => handleMarkReminderSent(item.id)}
                            className="btn btn-secondary btn-sm"
                            title="Send WhatsApp or Phone Reminder"
                          >
                            <Bell size={12} color="#f59e0b" />
                            <span>Send Reminder</span>
                          </button>
                        ) : (
                          <div style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--success)", fontSize: "12px" }}>
                            <CheckCircle2 size={14} />
                            <span>Ready</span>
                          </div>
                        )}
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
