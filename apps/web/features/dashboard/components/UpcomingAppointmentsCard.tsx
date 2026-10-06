"use client";

import React from "react";
import Link from "next/link";
import { Calendar, Clock, Video, Phone, MessageSquare, ExternalLink, CheckCircle2, Bell } from "lucide-react";

interface UpcomingAppointmentsCardProps {
  appointments: any[];
}

export const UpcomingAppointmentsCard: React.FC<UpcomingAppointmentsCardProps> = ({ appointments }) => {
  const getChannelIcon = (pref: string) => {
    switch (pref?.toLowerCase()) {
      case "google meet":
        return <Video size={14} color="var(--primary)" />;
      case "whatsapp":
        return <MessageSquare size={14} color="var(--success)" />;
      default:
        return <Phone size={14} color="var(--accent)" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toUpperCase()) {
      case "CONFIRMED":
        return "badge-primary";
      case "COMPLETED":
        return "badge-success";
      case "CANCELLED":
        return "badge-danger";
      case "REMINDER_SCHEDULED":
      default:
        return "badge-warning";
    }
  };

  return (
    <div className="card" style={{ marginBottom: "24px" }}>
      <div className="card-header">
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "8px",
              background: "rgba(99, 102, 241, 0.15)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--primary)",
            }}
          >
            <Calendar size={18} />
          </div>
          <div>
            <h3 className="card-title" style={{ margin: 0 }}>Upcoming Demo Appointments</h3>
            <p style={{ fontSize: "12px", color: "var(--foreground-muted)", margin: 0 }}>
              Prospects converted by Madhu for custom software presentations
            </p>
          </div>
        </div>
        <Link href="/appointments" className="btn btn-secondary btn-sm">
          <span>Manage Appointments</span>
          <ExternalLink size={14} />
        </Link>
      </div>

      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Lead & Domain</th>
              <th>Date & Time</th>
              <th>Channel</th>
              <th>Status</th>
              <th>Reminder</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {appointments.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: "center", padding: "32px", color: "var(--foreground-muted)" }}>
                  No appointments booked yet. Conversational agent Madhu automatically schedules demos when prospects express interest.
                </td>
              </tr>
            ) : (
              appointments.map((apt) => (
                <tr key={apt.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{apt.lead?.full_name || "Lead Prospect"}</div>
                    <div style={{ fontSize: "12px", color: "var(--foreground-muted)" }}>
                      {apt.lead?.company || "Enterprise"} • <span style={{ color: "var(--accent)" }}>{apt.lead?.domain || apt.lead?.custom_data?.domain || "Custom Software"}</span>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <Clock size={13} color="var(--primary)" />
                      <span>{apt.scheduled_at ? new Date(apt.scheduled_at).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "TBD"}</span>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "13px" }}>
                      {getChannelIcon(apt.contact_channel)}
                      <span>{apt.contact_channel || "WhatsApp"}</span>
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${getStatusBadge(apt.status)}`}>
                      {apt.status}
                    </span>
                  </td>
                  <td>
                    {apt.reminder_sent ? (
                      <span style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--success)", fontSize: "12px" }}>
                        <CheckCircle2 size={14} />
                        Sent
                      </span>
                    ) : (
                      <span style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--warning)", fontSize: "12px" }}>
                        <Bell size={14} />
                        Pending
                      </span>
                    )}
                  </td>
                  <td>
                    <Link href="/appointments" className="btn btn-secondary btn-sm" style={{ padding: "4px 10px" }}>
                      Details
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
