"use client";

import React, { useState } from "react";
import { X } from "lucide-react";
import { leadsApi } from "../../../lib/api";

interface CreateLeadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export const CreateLeadModal: React.FC<CreateLeadModalProps> = ({
  isOpen,
  onClose,
  onCreated,
}) => {
  const [phone, setPhone] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [dnc, setDnc] = useState(false);
  const [saving, setSaving] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phone.trim()) return;

    setSaving(true);
    try {
      await leadsApi.create({
        phone: phone.trim(),
        full_name: fullName.trim() || undefined,
        email: email.trim() || undefined,
        company: company.trim() || undefined,
        do_not_call: dnc,
      });
      onCreated();
      onClose();
    } catch (err: any) {
      alert(err.message || "Failed to add lead");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-dialog">
        <div className="modal-header">
          <h3 style={{ fontSize: "17px", fontWeight: 600 }}>Add Individual Lead</h3>
          <button onClick={onClose} className="btn-icon">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-group">
              <label className="form-label">Phone Number *</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. +919876543210 or +14155552671"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Contact Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Rahul Sharma"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input
                type="email"
                className="form-input"
                placeholder="e.g. rahul@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Company Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. TechFlow Innovations"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
              />
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "14px" }}>
              <input
                type="checkbox"
                id="dncCheckbox"
                checked={dnc}
                onChange={(e) => setDnc(e.target.checked)}
                style={{ width: "16px", height: "16px", accentColor: "var(--danger)" }}
              />
              <label htmlFor="dncCheckbox" style={{ fontSize: "13px", color: "var(--foreground)" }}>
                Mark as Do-Not-Call (DNC) - Platform will prevent outbound calls to this number
              </label>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={saving} className="btn btn-primary">
              {saving ? "Saving..." : "Add Lead"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
