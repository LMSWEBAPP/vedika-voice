"use client";

import React from "react";
import styles from "../../../styles/dashboard.module.css";

interface OutcomesBreakdownChartProps {
  outcomes: Array<{
    status: string;
    count: number;
    percentage: number;
  }>;
}

export const OutcomesBreakdownChart: React.FC<OutcomesBreakdownChartProps> = ({ outcomes }) => {
  const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
      case "COMPLETED":
        return "#10b981";
      case "CONNECTED":
      case "IN_PROGRESS":
        return "#6366f1";
      case "RINGING":
      case "INITIATING":
        return "#06b6d4";
      case "NO_ANSWER":
        return "#f59e0b";
      case "BUSY":
        return "#f97316";
      case "FAILED":
        return "#ef4444";
      default:
        return "#8b9bb4";
    }
  };

  return (
    <div className={styles.chartCard}>
      <div className="card-header" style={{ marginBottom: "16px" }}>
        <h3 className="card-title">Call Outcomes</h3>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "14px", marginTop: "10px" }}>
        {outcomes.length === 0 ? (
          <div style={{ color: "var(--foreground-muted)", fontSize: "13px", padding: "20px 0" }}>
            No calls recorded yet.
          </div>
        ) : (
          outcomes.map((item, idx) => (
            <div key={idx}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", marginBottom: "5px" }}>
                <span style={{ fontWeight: 500, color: "var(--foreground)" }}>{item.status}</span>
                <span style={{ color: "var(--foreground-muted)" }}>
                  {item.count} ({item.percentage}%)
                </span>
              </div>
              <div style={{ height: "6px", background: "rgba(255,255,255,0.06)", borderRadius: "var(--radius-full)", overflow: "hidden" }}>
                <div
                  style={{
                    height: "100%",
                    width: `${Math.max(item.percentage, 3)}%`,
                    backgroundColor: getStatusColor(item.status),
                    borderRadius: "var(--radius-full)",
                  }}
                />
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
