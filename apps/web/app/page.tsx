"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { AppLayout } from "../components/layout/AppLayout";
import { Header } from "../components/layout/Header";
import { MetricsOverview } from "../features/dashboard/components/MetricsOverview";
import { CallsTrendChart } from "../features/dashboard/components/CallsTrendChart";
import { OutcomesBreakdownChart } from "../features/dashboard/components/OutcomesBreakdownChart";
import { RecentCallsTable } from "../features/dashboard/components/RecentCallsTable";
import { UpcomingAppointmentsCard } from "../features/dashboard/components/UpcomingAppointmentsCard";
import { analyticsApi, callsApi, appointmentsApi } from "../lib/api";
import { Megaphone, Upload, Bot, RefreshCw, Calendar } from "lucide-react";
import styles from "../styles/dashboard.module.css";

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<any>(null);
  const [recentCalls, setRecentCalls] = useState<any[]>([]);
  const [recentAppointments, setRecentAppointments] = useState<any[]>([]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [analyticsData, callsData, appointmentsData] = await Promise.all([
        analyticsApi.getOverview(),
        callsApi.list({ limit: 6 }),
        appointmentsApi.list({ limit: 5 }),
      ]);
      setOverview(analyticsData);
      setRecentCalls(callsData);
      setRecentAppointments(appointmentsData);
    } catch (err: any) {
      console.error("Dashboard data load error:", err);
      setError(err.message || "Failed to load dashboard statistics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <AppLayout>
      <Header
        title="Voice Calling Operations"
        subtitle="Real-time outbound campaign monitoring, conversion analytics, and call intelligence"
        actions={
          <button onClick={loadData} className="btn btn-secondary btn-sm" title="Refresh">
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
        }
      />

      <main className={styles.contentContainer || "content-container"} style={{ padding: "32px", maxWidth: "1440px", margin: "0 auto" }}>
        {/* Quick Action Navigation Bar */}
        <div className={styles.quickActionsBar}>
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <Link href="/campaigns" className="btn btn-primary">
              <Megaphone size={16} />
              <span>Launch Campaign</span>
            </Link>
            <Link href="/leads" className="btn btn-secondary">
              <Upload size={16} />
              <span>Import Leads</span>
            </Link>
            <Link href="/agent-builder" className="btn btn-secondary" style={{ borderColor: "rgba(99, 102, 241, 0.4)" }}>
              <Bot size={16} color="var(--primary)" />
              <span>In-Browser Live Mic Tester</span>
            </Link>
            <Link href="/appointments" className="btn btn-secondary" style={{ borderColor: "rgba(16, 185, 129, 0.4)" }}>
              <Calendar size={16} color="var(--success)" />
              <span>Booked Demos ({recentAppointments.length})</span>
            </Link>
          </div>
        </div>

        {loading ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            <div className="skeleton" style={{ height: "120px", width: "100%" }} />
            <div className="skeleton" style={{ height: "300px", width: "100%" }} />
          </div>
        ) : error ? (
          <div className="card" style={{ textAlign: "center", padding: "40px", borderColor: "var(--danger)" }}>
            <p style={{ color: "var(--danger)", marginBottom: "16px" }}>{error}</p>
            <button onClick={loadData} className="btn btn-primary btn-sm">
              Retry Connection
            </button>
          </div>
        ) : (
          <div className="animate-fade-in">
            {/* 1. Metrics Cards */}
            <MetricsOverview metrics={overview?.summary || {}} />

            {/* 2. Charts Grid */}
            <div className={styles.chartsGrid}>
              <CallsTrendChart data={overview?.calls_over_time || []} />
              <OutcomesBreakdownChart outcomes={overview?.outcomes || []} />
            </div>

            {/* 3. Upcoming Demo Appointments */}
            <UpcomingAppointmentsCard appointments={recentAppointments} />

            {/* 4. Recent Calls Table */}
            <RecentCallsTable calls={recentCalls} />
          </div>
        )}
      </main>
    </AppLayout>
  );
}
