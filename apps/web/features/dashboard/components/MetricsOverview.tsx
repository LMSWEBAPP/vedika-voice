"use client";

import React from "react";
import { Users, PhoneCall, CheckCircle2, TrendingUp, Clock, UserCheck } from "lucide-react";
import styles from "../../../styles/dashboard.module.css";

interface MetricsOverviewProps {
  metrics: {
    total_leads: number;
    calls_made: number;
    answered_calls: number;
    completed_calls: number;
    interested_leads: number;
    average_duration_seconds: number;
    conversion_rate: number;
  };
}

export const MetricsOverview: React.FC<MetricsOverviewProps> = ({ metrics }) => {
  const cards = [
    {
      title: "Total Leads",
      value: metrics.total_leads.toLocaleString(),
      subtext: "Total leads imported",
      icon: Users,
      color: "#6366f1",
      bgColor: "rgba(99, 102, 241, 0.12)",
    },
    {
      title: "Calls Placed",
      value: metrics.calls_made.toLocaleString(),
      subtext: `${metrics.answered_calls} answered by recipient`,
      icon: PhoneCall,
      color: "#06b6d4",
      bgColor: "rgba(6, 182, 212, 0.12)",
    },
    {
      title: "Completed Calls",
      value: metrics.completed_calls.toLocaleString(),
      subtext: `${metrics.calls_made > 0 ? Math.round((metrics.completed_calls / metrics.calls_made) * 100) : 0}% completion rate`,
      icon: CheckCircle2,
      color: "#10b981",
      bgColor: "rgba(16, 185, 129, 0.12)",
    },
    {
      title: "Interested Leads",
      value: metrics.interested_leads.toLocaleString(),
      subtext: `${metrics.conversion_rate}% conversion rate`,
      icon: UserCheck,
      color: "#ec4899",
      bgColor: "rgba(236, 72, 153, 0.12)",
    },
    {
      title: "Avg Call Duration",
      value: `${Math.round(metrics.average_duration_seconds)}s`,
      subtext: "Effective conversation time",
      icon: Clock,
      color: "#f59e0b",
      bgColor: "rgba(245, 158, 11, 0.12)",
    },
  ];

  return (
    <div className={styles.metricsGrid}>
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <div key={i} className={styles.metricCard}>
            <div className={styles.metricHeader}>
              <span className={styles.metricTitle}>{c.title}</span>
              <div className={styles.metricIcon} style={{ background: c.bgColor, color: c.color }}>
                <Icon size={18} />
              </div>
            </div>
            <div className={styles.metricValue}>{c.value}</div>
            <div className={styles.metricSubtext}>{c.subtext}</div>
          </div>
        );
      })}
    </div>
  );
};
