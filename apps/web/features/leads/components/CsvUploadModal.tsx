"use client";

import React, { useState } from "react";
import { X, Upload, CheckCircle2, AlertCircle } from "lucide-react";
import { leadsApi } from "../../../lib/api";

interface CsvUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  campaigns?: any[];
}

export const CsvUploadModal: React.FC<CsvUploadModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  campaigns = [],
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [campaignId, setCampaignId] = useState("");
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);

  if (!isOpen) return null;

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setResult(null);
    try {
      const res = await leadsApi.uploadCSV(file, campaignId || undefined);
      setResult(res);
      onSuccess();
    } catch (err: any) {
      alert(err.message || "Failed to upload CSV");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-dialog">
        <div className="modal-header">
          <h3 style={{ fontSize: "17px", fontWeight: 600 }}>Import Leads via CSV</h3>
          <button onClick={onClose} className="btn-icon">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleUpload}>
          <div className="modal-body">
            <p style={{ fontSize: "13px", color: "var(--foreground-muted)", marginBottom: "16px" }}>
              Upload a standard CSV file with headers: <code style={{ color: "var(--primary)" }}>phone, full_name, email, company, do_not_call</code>.
              Duplicates and DNC records are automatically detected and verified.
            </p>

            <div className="form-group">
              <label className="form-label">Select CSV File *</label>
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Assign to Campaign (Optional)</label>
              <select
                className="form-select"
                value={campaignId}
                onChange={(e) => setCampaignId(e.target.value)}
              >
                <option value="">Do not assign to a campaign now</option>
                {campaigns.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            {result && (
              <div
                style={{
                  background: "rgba(16, 185, 129, 0.1)",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                  padding: "16px",
                  borderRadius: "var(--radius-md)",
                  marginTop: "16px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--success)", fontWeight: 600, marginBottom: "8px" }}>
                  <CheckCircle2 size={18} />
                  <span>Import Completed</span>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "13px" }}>
                  <div>Total Processed: <strong>{result.total_processed}</strong></div>
                  <div style={{ color: "var(--success)" }}>Imported: <strong>{result.imported}</strong></div>
                  <div style={{ color: "var(--warning)" }}>Duplicates: <strong>{result.skipped_duplicates}</strong></div>
                  <div style={{ color: "var(--danger)" }}>DNC Flags: <strong>{result.rejected_dnc}</strong></div>
                  <div>Invalid Format: <strong>{result.invalid_format}</strong></div>
                </div>
              </div>
            )}
          </div>

          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              {result ? "Close" : "Cancel"}
            </button>
            {!result && (
              <button type="submit" disabled={uploading || !file} className="btn btn-primary">
                {uploading ? "Uploading & Validating..." : "Start Import"}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};
