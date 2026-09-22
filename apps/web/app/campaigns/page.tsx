"use client";

import React, { useEffect, useState } from "react";
import { AppLayout } from "../../components/layout/AppLayout";
import { Header } from "../../components/layout/Header";
import { CampaignCard } from "../../features/campaigns/components/CampaignCard";
import { CampaignModal } from "../../features/campaigns/components/CampaignModal";
import { campaignsApi } from "../../lib/api";
import { Plus, Megaphone, RefreshCw } from "lucide-react";
import styles from "../../styles/campaigns.module.css";

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  const loadCampaigns = async () => {
    setLoading(true);
    try {
      const data = await campaignsApi.list();
      setCampaigns(data);
    } catch (err: any) {
      console.error("Failed to load campaigns:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCampaigns();
  }, []);

  return (
    <AppLayout>
      <Header
        title="Calling Campaigns"
        subtitle="Configure, launch, pause, and track outbound AI voice campaigns"
        actions={
          <button onClick={() => setModalOpen(true)} className="btn btn-primary btn-sm">
            <Plus size={16} />
            <span>Create Campaign</span>
          </button>
        }
      />

      <main style={{ padding: "32px", maxWidth: "1440px", margin: "0 auto" }}>
        {loading ? (
          <div className={styles.campaignsGrid}>
            <div className="skeleton" style={{ height: "200px" }} />
            <div className="skeleton" style={{ height: "200px" }} />
          </div>
        ) : campaigns.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: "60px 20px" }}>
            <Megaphone size={42} style={{ margin: "0 auto 16px", color: "var(--foreground-muted)" }} />
            <h3 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "8px" }}>No campaigns yet</h3>
            <p style={{ color: "var(--foreground-muted)", maxWidth: "420px", margin: "0 auto 20px", fontSize: "14px" }}>
              Create your first voice campaign to define your conversational AI script, add leads, and start calling.
            </p>
            <button onClick={() => setModalOpen(true)} className="btn btn-primary">
              <Plus size={16} />
              <span>Create Campaign</span>
            </button>
          </div>
        ) : (
          <div className={styles.campaignsGrid}>
            {campaigns.map((camp) => (
              <CampaignCard key={camp.id} campaign={camp} onRefresh={loadCampaigns} />
            ))}
          </div>
        )}

        <CampaignModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          onCreated={loadCampaigns}
        />
      </main>
    </AppLayout>
  );
}
