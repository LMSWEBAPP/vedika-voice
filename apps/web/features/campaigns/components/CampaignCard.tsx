"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Play, Pause, Square, Bot, ArrowRight } from "lucide-react";
import styles from "../../../styles/campaigns.module.css";
import { campaignsApi } from "../../../lib/api";

interface CampaignCardProps {
  campaign: any;
  onRefresh: () => void;
}

export const CampaignCard: React.FC<CampaignCardProps> = ({ campaign, onRefresh }) => {
  const [updating, setUpdating] = useState(false);

  const handleStatusChange = async (action: "start" | "pause" | "stop") => {
    setUpdating(true);
    try {
      if (action === "start") await campaignsApi.start(campaign.id);
      else if (action === "pause") await campaignsApi.pause(campaign.id);
      else if (action === "stop") await campaignsApi.stop(campaign.id);
      onRefresh();
    } catch (err: any) {
      alert(err.message || "Failed to update campaign status");
    } finally {
      setUpdating(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case "ACTIVE":
        return <span className="badge badge-success">Active</span>;
      case "PAUSED":
        return <span className="badge badge-warning">Paused</span>;
      case "COMPLETED":
        return <span className="badge badge-info">Completed</span>;
      default:
        return <span className="badge badge-neutral">Draft</span>;
    }
  };

  const stats = campaign.stats || { total_leads: 0, calls_completed: 0, interested_count: 0 };

  return (
    <div className={styles.campaignCard}>
      <div>
        <div className={styles.cardHeader}>
          <div>
            <h3 className={styles.campaignName}>{campaign.name}</h3>
            <p className={styles.campaignDesc}>{campaign.objective}</p>
          </div>
          {getStatusBadge(campaign.status)}
        </div>

        <div className={styles.statsBar}>
          <div>
            <div className={styles.statItemTitle}>Assigned Leads</div>
            <div className={styles.statItemValue}>{stats.total_leads}</div>
          </div>
          <div>
            <div className={styles.statItemTitle}>Calls Done</div>
            <div className={styles.statItemValue}>{stats.calls_completed}</div>
          </div>
          <div>
            <div className={styles.statItemTitle}>Interested</div>
            <div className={styles.statItemValue} style={{ color: "var(--success)" }}>
              {stats.interested_count}
            </div>
          </div>
        </div>
      </div>

      <div className={styles.cardFooter}>
        <div style={{ display: "flex", gap: "8px" }}>
          {campaign.status !== "ACTIVE" ? (
            <button
              onClick={() => handleStatusChange("start")}
              disabled={updating}
              className="btn btn-primary btn-sm"
              title="Start Campaign Calls"
            >
              <Play size={13} />
              <span>Start</span>
            </button>
          ) : (
            <button
              onClick={() => handleStatusChange("pause")}
              disabled={updating}
              className="btn btn-secondary btn-sm"
              title="Pause Campaign"
            >
              <Pause size={13} />
              <span>Pause</span>
            </button>
          )}

          {campaign.status === "ACTIVE" && (
            <button
              onClick={() => handleStatusChange("stop")}
              disabled={updating}
              className="btn btn-danger btn-sm"
              title="Stop Campaign"
            >
              <Square size={13} />
              <span>Stop</span>
            </button>
          )}

          <Link href={`/agent-builder?campaignId=${campaign.id}`} className="btn btn-secondary btn-sm" title="Configure AI Script">
            <Bot size={13} />
            <span>Script</span>
          </Link>
        </div>

        <Link href={`/campaigns/${campaign.id}`} className="btn btn-secondary btn-sm" style={{ padding: "6px" }}>
          <ArrowRight size={16} />
        </Link>
      </div>
    </div>
  );
};
