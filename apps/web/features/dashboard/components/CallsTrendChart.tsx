"use client";

import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import styles from "../../../styles/dashboard.module.css";

interface CallsTrendChartProps {
  data: Array<{
    date: string;
    total: number;
    completed: number;
    interested: number;
  }>;
}

export const CallsTrendChart: React.FC<CallsTrendChartProps> = ({ data }) => {
  return (
    <div className={styles.chartCard}>
      <div className="card-header" style={{ marginBottom: "16px" }}>
        <h3 className="card-title">Call Volume & Outcomes Trend</h3>
        <span style={{ fontSize: "12px", color: "var(--foreground-muted)" }}>Last 7 Days</span>
      </div>

      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="totalCallsGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="completedGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
            <XAxis dataKey="date" stroke="var(--foreground-subtle)" fontSize={11} tickLine={false} />
            <YAxis stroke="var(--foreground-subtle)" fontSize={11} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--background-secondary)",
                borderColor: "var(--border)",
                borderRadius: "var(--radius-md)",
                color: "var(--foreground)",
                fontSize: "12px",
              }}
            />
            <Area
              type="monotone"
              dataKey="total"
              name="Total Placed"
              stroke="#6366f1"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#totalCallsGradient)"
            />
            <Area
              type="monotone"
              dataKey="completed"
              name="Completed"
              stroke="#10b981"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#completedGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
