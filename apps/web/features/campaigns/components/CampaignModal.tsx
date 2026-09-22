"use client";

import React, { useState } from "react";
import { X } from "lucide-react";
import { campaignsApi } from "../../../lib/api";

interface CampaignModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export const CampaignModal: React.FC<CampaignModalProps> = ({ isOpen, onClose, onCreated }) => {
  const [name, setName] = useState("");
  const [objective, setObjective] = useState("");
  const [language, setLanguage] = useState("en");
  const [opening, setOpening] = useState("Hello, thank you for answering my call!");
  const [persona, setPersona] = useState("Professional, consultative, and courteous representative.");
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !objective.trim()) return;

    setSubmitting(true);
    try {
      await campaignsApi.create({
        name,
        objective,
        primary_language: language,
        fallback_language: "en",
        script: {
          opening,
          objective,
          persona,
          voice_name: "Aoede",
          questions: [
            {
              id: "q1_interested",
              text: "Are you interested in exploring this further?",
              type: "boolean",
              required: true,
            },
          ],
          closing: "Thank you for your time. Have a great day!",
        },
      });
      onCreated();
      onClose();
    } catch (err: any) {
      alert(err.message || "Failed to create campaign");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-dialog">
        <div className="modal-header">
          <h3 style={{ fontSize: "17px", fontWeight: 600 }}>Create New Outbound Campaign</h3>
          <button onClick={onClose} className="btn-icon">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-group">
              <label className="form-label">Campaign Name *</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Enterprise Q1 Lead Qualification"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Campaign Objective *</label>
              <textarea
                className="form-textarea"
                rows={2}
                placeholder="What is the high-level purpose of this voice call?"
                value={objective}
                onChange={(e) => setObjective(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">AI Agent Persona</label>
              <input
                type="text"
                className="form-input"
                value={persona}
                onChange={(e) => setPersona(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Opening Greeting Line</label>
              <textarea
                className="form-textarea"
                rows={2}
                value={opening}
                onChange={(e) => setOpening(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Primary Call Language</label>
              <select className="form-select" value={language} onChange={(e) => setLanguage(e.target.value)}>
                <option value="en">English (Global / US)</option>
                <option value="hi">Hindi</option>
                <option value="te">Telugu</option>
                <option value="kn">Kannada</option>
                <option value="ta">Tamil</option>
              </select>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={submitting} className="btn btn-primary">
              {submitting ? "Creating..." : "Create Campaign"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
