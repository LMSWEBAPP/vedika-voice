"use client";

import React from "react";
import Link from "next/link";
import { ExternalLink, Phone } from "lucide-react";

interface RecentCallsTableProps {
  calls: any[];
}

export const RecentCallsTable: React.FC<RecentCallsTableProps> = ({ calls }) => {
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
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">
          <Phone size={18} color="var(--primary)" />
          Recent Voice Calls
        </h3>
        <Link href="/calls" className="btn btn-secondary btn-sm">
          <span>View All Calls</span>
          <ExternalLink size={14} />
        </Link>
      </div>

      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Lead Name</th>
              <th>Phone</th>
              <th>Status</th>
              <th>Duration</th>
              <th>Provider</th>
              <th>Timestamp</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {calls.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: "center", padding: "32px", color: "var(--foreground-muted)" }}>
                  No voice calls placed yet. Start a campaign or initiate a call to see live status.
                </td>
              </tr>
            ) : (
              calls.map((call) => (
                <tr key={call.id}>
                  <td style={{ fontWeight: 600 }}>{call.lead?.full_name || "Anonymous Contact"}</td>
                  <td style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: "var(--foreground-muted)" }}>
                    {call.lead?.phone || "N/A"}
                  </td>
                  <td>
                    <span className={`badge ${getBadgeClass(call.status)}`}>
                      {call.status}
                    </span>
                  </td>
                  <td>{call.duration_seconds > 0 ? `${call.duration_seconds}s` : "--"}</td>
                  <td style={{ textTransform: "capitalize" }}>{call.provider}</td>
                  <td style={{ color: "var(--foreground-muted)", fontSize: "13px" }}>
                    {new Date(call.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </td>
                  <td>
                    <Link href={`/calls/${call.id}`} className="btn btn-secondary btn-sm" style={{ padding: "4px 10px" }}>
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
  );
};
