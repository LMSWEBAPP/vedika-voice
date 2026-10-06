"use client";

import React, { useState, useRef, useEffect } from "react";
import * as XLSX from "xlsx";
import {
  FileSpreadsheet,
  Upload,
  Download,
  Plus,
  Trash2,
  PhoneCall,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Check,
  Mic,
  Loader2,
  Info,
} from "lucide-react";
import { callsApi } from "../../../lib/api";
import styles from "../../../styles/spreadsheet.module.css";

export interface SpreadsheetLead {
  id: string;
  name: string;
  phone: string;
  company: string;
  industry: string;
  pitchGoal: string;
  notes: string;
  city: string;
  dealValue: string;
  status: "new" | "qualified" | "calling" | "contacted" | "dnc";
}

// Single clean initial row with the user's verified test phone number (no demo data)
export const INITIAL_LEADS: SpreadsheetLead[] = [
  {
    id: "lead_1",
    name: "Lead Contact",
    phone: "+917981104636",
    company: "Target Business",
    industry: "General Business",
    pitchGoal: "Modern responsive web application with 24/7 automated customer inquiries",
    notes: "Direct lead for real outbound calling test.",
    city: "Hyderabad",
    dealValue: "Standard",
    status: "new",
  },
];

interface LeadsSpreadsheetGridProps {
  onSelectLead?: (lead: SpreadsheetLead) => void;
  activeLeadId?: string;
  onBrowserMicCall?: (lead: SpreadsheetLead) => void;
  onCallNow?: (lead: SpreadsheetLead) => void;
}

export const LeadsSpreadsheetGrid: React.FC<LeadsSpreadsheetGridProps> = ({
  onSelectLead,
  activeLeadId,
  onBrowserMicCall,
  onCallNow,
}) => {
  const [leads, setLeads] = useState<SpreadsheetLead[]>(INITIAL_LEADS);
  const [selectedId, setSelectedId] = useState<string>(activeLeadId || INITIAL_LEADS[0].id);
  const [expandedRowId, setExpandedRowId] = useState<string | null>(null);
  const [notification, setNotification] = useState<string | null>(null);
  const [isCallingPhone, setIsCallingPhone] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (activeLeadId) {
      setSelectedId(activeLeadId);
    }
  }, [activeLeadId]);

  const activeLead = leads.find((l) => l.id === selectedId) || leads[0];

  const showToast = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 5000);
  };

  const handleCellChange = (id: string, field: keyof SpreadsheetLead, value: string) => {
    setLeads((prev) =>
      prev.map((item) => {
        if (item.id === id) {
          const updated = { ...item, [field]: value };
          if (updated.id === selectedId && onSelectLead) {
            onSelectLead(updated);
          }
          return updated;
        }
        return item;
      })
    );
  };

  const handleAddRow = () => {
    const newLead: SpreadsheetLead = {
      id: `lead_${Date.now()}`,
      name: "",
      phone: "+91",
      company: "",
      industry: "General",
      pitchGoal: "Modern web solution to increase sales and streamline operations",
      notes: "",
      city: "",
      dealValue: "",
      status: "new",
    };
    setLeads((prev) => [...prev, newLead]);
    setSelectedId(newLead.id);
    setExpandedRowId(newLead.id);
    if (onSelectLead) onSelectLead(newLead);
    showToast("Added new lead row. Enter Name, Company, and Phone.");
  };

  const handleDeleteRow = (id: string) => {
    if (leads.length <= 1) {
      alert("At least one lead is required in the sheet.");
      return;
    }
    const filtered = leads.filter((l) => l.id !== id);
    setLeads(filtered);
    if (selectedId === id) {
      const nextActive = filtered[0];
      setSelectedId(nextActive.id);
      if (onSelectLead) onSelectLead(nextActive);
    }
    showToast("Lead row deleted.");
  };

  const handleSelectRow = (lead: SpreadsheetLead) => {
    setSelectedId(lead.id);
    if (onSelectLead) onSelectLead(lead);
    showToast(`Active Lead set to: ${lead.name || "Lead"} (${lead.company || "Company"})`);
  };

  const toggleExpand = (id: string) => {
    setExpandedRowId((prev) => (prev === id ? null : id));
  };

  /**
   * Place real outbound carrier phone call to lead's phone number
   */
  const handleCallRealPhone = async (lead: SpreadsheetLead) => {
    if (!lead.phone || lead.phone.trim().length < 8) {
      alert("Please enter a valid phone number with country code (e.g. +917981104636).");
      return;
    }

    setIsCallingPhone(lead.id);
    showToast(`Initiating outbound call to ${lead.phone} via Twilio...`);

    try {
      const res = await callsApi.directCall({
        phone: lead.phone,
        name: lead.name,
        company: lead.company,
        pitch_goal: lead.pitchGoal,
        notes: lead.notes,
      });

      showToast(`📞 Dialing ${lead.phone} via Twilio! Pick up your phone.`);
      alert(`Success! Twilio is calling ${lead.phone}.\n\nStatus: ${res.status}\nCall SID: ${res.provider_call_id}\n\nYour mobile phone will ring right now!`);
    } catch (err: any) {
      console.error("Direct call error:", err);
      alert(`Call failed: ${err.message || "Could not reach carrier API"}`);
    } finally {
      setIsCallingPhone(null);
    }
  };

  /**
   * Import Excel (.xlsx, .xls) or CSV file
   */
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const bstr = evt.target?.result;
        const workbook = XLSX.read(bstr, { type: "binary" });
        const firstSheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[firstSheetName];
        const rawJson: any[] = XLSX.utils.sheet_to_json(worksheet, { defval: "" });

        if (!rawJson || rawJson.length === 0) {
          alert("No rows found in the uploaded file.");
          return;
        }

        const parsedLeads: SpreadsheetLead[] = rawJson.map((row, idx) => {
          const findVal = (keys: string[]): string => {
            for (const k of Object.keys(row)) {
              const cleanKey = k.toLowerCase().replace(/[^a-z0-9]/g, "");
              if (keys.includes(cleanKey)) {
                return String(row[k] || "").trim();
              }
            }
            return "";
          };

          const name =
            findVal(["name", "fullname", "contact", "prospectname", "clientname", "leadname"]) ||
            `Lead #${idx + 1}`;
          const phone =
            findVal(["phone", "phonenumber", "mobile", "contactnumber", "cell"]) || "+917981104636";
          const company =
            findVal(["company", "businessname", "business", "clinic", "firm", "store"]) || "Business";
          const industry =
            findVal(["industry", "businesstype", "category", "sector", "type"]) || "General";
          const pitchGoal =
            findVal(["pitchgoal", "pitch", "goal", "solution", "valueprop", "objective"]) ||
            "Modern web solution with automated customer inquiries";
          const notes =
            findVal(["notes", "painpoints", "intel", "details", "comments", "remarks", "context"]) || "";
          const city = findVal(["city", "location", "state", "place"]) || "";
          const dealValue = findVal(["dealvalue", "value", "budget", "amount", "ticket", "dealsize"]) || "";

          return {
            id: `imported_${Date.now()}_${idx}`,
            name,
            phone,
            company,
            industry,
            pitchGoal,
            notes,
            city,
            dealValue,
            status: "new",
          };
        });

        setLeads(parsedLeads);
        setSelectedId(parsedLeads[0].id);
        if (onSelectLead) onSelectLead(parsedLeads[0]);
        showToast(`Successfully loaded ${parsedLeads.length} leads from "${file.name}"!`);
      } catch (err: any) {
        console.error("Excel parse error:", err);
        alert(`Failed to parse file: ${err.message || "Unknown error"}`);
      } finally {
        if (fileInputRef.current) fileInputRef.current.value = "";
      }
    };
    reader.readAsBinaryString(file);
  };

  /**
   * Export current leads as an Excel file
   */
  const handleExportExcel = () => {
    const exportData = leads.map((l) => ({
      "Full Name": l.name,
      "Phone Number": l.phone,
      "Business / Company": l.company,
      "Industry": l.industry,
      "Pitch Goal / Solution": l.pitchGoal,
      "Pain Points & Notes": l.notes,
      "City": l.city,
      "Deal Value": l.dealValue,
    }));

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Veyra Leads");
    XLSX.writeFile(workbook, `Veyra_Leads_${new Date().toISOString().slice(0, 10)}.xlsx`);
    showToast("Downloaded current leads spreadsheet.");
  };

  /**
   * Download a blank clean template
   */
  const handleDownloadTemplate = () => {
    const templateData = [
      {
        "Full Name": "Contact Name",
        "Phone Number": "+917981104636",
        "Business / Company": "Company Name",
        "Industry": "Technology / Healthcare / Retail",
        "Pitch Goal / Solution": "Online booking and customer automation web app",
        "Pain Points & Notes": "High manual call overhead, needs digital booking",
        "City": "Hyderabad",
        "Deal Value": "Standard",
      },
    ];

    const worksheet = XLSX.utils.json_to_sheet(templateData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Lead Template");
    XLSX.writeFile(workbook, "Veyra_Leads_Template.xlsx");
    showToast("Template downloaded! Fill in Excel and re-import anytime.");
  };

  return (
    <div className={styles.container}>
      {/* Top Action Bar */}
      <div className={styles.topBar}>
        <div className={styles.titleArea}>
          <FileSpreadsheet size={22} color="var(--accent-cyan)" />
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <h3 style={{ fontSize: "16px", fontWeight: 700, margin: 0, color: "var(--foreground)" }}>
                Lead Call Sheet
              </h3>
              <span className={styles.badge}>Live Caller</span>
            </div>
            <p style={{ fontSize: "12px", color: "var(--foreground-muted)", margin: "2px 0 0 0" }}>
              Name, Business &amp; Phone are visible. Click <strong>Details</strong> to view/edit pitch &amp; notes. Click <strong>Call Phone</strong> to ring your real mobile!
            </p>
          </div>
        </div>

        <div className={styles.actionsGroup}>
          <div className={styles.fileInputWrapper}>
            <button className="btn btn-secondary btn-sm" title="Import real leads from CSV or Excel">
              <Upload size={14} />
              <span>Import CSV / Excel</span>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls,.csv"
              className={styles.hiddenFileInput}
              onChange={handleFileUpload}
            />
          </div>

          <button onClick={handleDownloadTemplate} className="btn btn-secondary btn-sm" title="Download Excel template">
            <Download size={14} />
            <span>Template</span>
          </button>

          <button onClick={handleExportExcel} className="btn btn-secondary btn-sm" title="Export current sheet">
            <FileSpreadsheet size={14} />
            <span>Export (.xlsx)</span>
          </button>

          <button onClick={handleAddRow} className="btn btn-primary btn-sm" title="Add new lead row">
            <Plus size={14} />
            <span>Add Row</span>
          </button>
        </div>
      </div>

      {/* Active Lead Summary Banner */}
      {activeLead && (
        <div className={styles.activeBanner}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div className={styles.activeBadge}>
              <span className={styles.pulseDot}></span>
              <span>ACTIVE PROSPECT</span>
            </div>
            <div style={{ fontSize: "13px", color: "var(--foreground)" }}>
              <strong>{activeLead.name || "Lead"}</strong> &mdash; {activeLead.company || "Business"} &bull;{" "}
              <span style={{ fontFamily: "var(--font-mono)", color: "var(--accent-cyan)" }}>
                {activeLead.phone}
              </span>
            </div>
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            <button
              onClick={() => handleCallRealPhone(activeLead)}
              disabled={isCallingPhone === activeLead.id}
              className={styles.callPhoneBtn}
              style={{ background: "#10b981", color: "#000", fontWeight: 700 }}
              title="Place a real phone call to this number via Twilio carrier"
            >
              {isCallingPhone === activeLead.id ? <Loader2 size={13} className="spin" /> : <PhoneCall size={13} />}
              <span>Call Real Phone ({activeLead.phone})</span>
            </button>

            {onBrowserMicCall && (
              <button
                onClick={() => onBrowserMicCall(activeLead)}
                className={styles.browserMicBtn}
                title="Test with your browser microphone"
              >
                <Mic size={13} />
                <span>Browser AI Pitch</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Streamlined Clean Table */}
      <div className={styles.tableWrapper}>
        <table className={styles.spreadsheetTable}>
          <thead>
            <tr>
              <th style={{ width: "45px", textAlign: "center" }}>#</th>
              <th style={{ width: "22%" }}>Prospect Name</th>
              <th style={{ width: "24%" }}>Business / Company</th>
              <th style={{ width: "20%" }}>Phone Number</th>
              <th style={{ width: "100px", textAlign: "center" }}>Details</th>
              <th style={{ width: "230px", textAlign: "center" }}>Actions</th>
              <th style={{ width: "45px", textAlign: "center" }}>Del</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead, idx) => {
              const isActive = lead.id === selectedId;
              const isExpanded = expandedRowId === lead.id;

              return (
                <React.Fragment key={lead.id}>
                  <tr className={isActive ? styles.rowActive : styles.rowNormal}>
                    <td style={{ textAlign: "center" }}>
                      <button
                        onClick={() => handleSelectRow(lead)}
                        className={`${styles.rowSelectBtn} ${isActive ? styles.rowSelectBtnActive : ""}`}
                        title={isActive ? "Active selected lead" : "Click to select"}
                      >
                        {isActive ? <Check size={12} /> : idx + 1}
                      </button>
                    </td>
                    <td>
                      <input
                        type="text"
                        className={styles.cellInput}
                        value={lead.name}
                        onChange={(e) => handleCellChange(lead.id, "name", e.target.value)}
                        placeholder="e.g. Rahul Verma"
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        className={styles.cellInput}
                        value={lead.company}
                        onChange={(e) => handleCellChange(lead.id, "company", e.target.value)}
                        placeholder="e.g. Apex Enterprises"
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        className={styles.cellInput}
                        style={{ fontFamily: "var(--font-mono)", color: "var(--accent-cyan)", fontWeight: 600 }}
                        value={lead.phone}
                        onChange={(e) => handleCellChange(lead.id, "phone", e.target.value)}
                        placeholder="+91..."
                      />
                    </td>
                    <td style={{ textAlign: "center" }}>
                      <button
                        onClick={() => toggleExpand(lead.id)}
                        className={`${styles.toggleDetailsBtn} ${isExpanded ? styles.toggleDetailsBtnActive : ""}`}
                        title={isExpanded ? "Collapse pitch details" : "Expand pitch details"}
                      >
                        <span>{isExpanded ? "Hide" : "Details"}</span>
                        {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                      </button>
                    </td>
                    <td style={{ textAlign: "center" }}>
                      <div style={{ display: "flex", gap: "6px", justifyContent: "center" }}>
                        <button
                          onClick={() => handleCallRealPhone(lead)}
                          disabled={isCallingPhone === lead.id}
                          className={styles.callPhoneBtn}
                          title="Dial real phone via Twilio"
                        >
                          {isCallingPhone === lead.id ? <Loader2 size={12} className="spin" /> : <PhoneCall size={12} />}
                          <span>Call Phone</span>
                        </button>
                        {onBrowserMicCall && (
                          <button
                            onClick={() => onBrowserMicCall(lead)}
                            className={styles.browserMicBtn}
                            title="Test via browser mic"
                          >
                            <Mic size={12} />
                            <span>Mic</span>
                          </button>
                        )}
                      </div>
                    </td>
                    <td style={{ textAlign: "center" }}>
                      <button
                        onClick={() => handleDeleteRow(lead.id)}
                        className={styles.deleteBtn}
                        title="Delete lead"
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>

                  {/* Collapsible Details Drawer */}
                  {isExpanded && (
                    <tr className={styles.detailsDrawerRow}>
                      <td colSpan={7}>
                        <div className={styles.detailsDrawerContent}>
                          <div className={styles.drawerField}>
                            <label className={styles.drawerLabel}>Pitch Goal / Value Proposition</label>
                            <textarea
                              className={styles.drawerTextarea}
                              value={lead.pitchGoal}
                              onChange={(e) => handleCellChange(lead.id, "pitchGoal", e.target.value)}
                              placeholder="What should Veyra AI offer to this business?"
                            />
                          </div>

                          <div className={styles.drawerField}>
                            <label className={styles.drawerLabel}>Pain Points &amp; Notes (AI Context)</label>
                            <textarea
                              className={styles.drawerTextarea}
                              value={lead.notes}
                              onChange={(e) => handleCellChange(lead.id, "notes", e.target.value)}
                              placeholder="Specific prospect intel, competitor challenges, or instructions..."
                            />
                          </div>

                          <div className={styles.drawerSubGrid}>
                            <div className={styles.drawerField}>
                              <label className={styles.drawerLabel}>Industry / Type</label>
                              <input
                                type="text"
                                className={styles.cellInput}
                                value={lead.industry}
                                onChange={(e) => handleCellChange(lead.id, "industry", e.target.value)}
                                placeholder="e.g. Healthcare / Retail"
                              />
                            </div>
                            <div className={styles.drawerField}>
                              <label className={styles.drawerLabel}>City / Location</label>
                              <input
                                type="text"
                                className={styles.cellInput}
                                value={lead.city}
                                onChange={(e) => handleCellChange(lead.id, "city", e.target.value)}
                                placeholder="e.g. Mumbai"
                              />
                            </div>
                            <div className={styles.drawerField}>
                              <label className={styles.drawerLabel}>Target Deal Value</label>
                              <input
                                type="text"
                                className={styles.cellInput}
                                value={lead.dealValue}
                                onChange={(e) => handleCellChange(lead.id, "dealValue", e.target.value)}
                                placeholder="₹50,000"
                              />
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Bottom Summary Bar */}
      <div className={styles.bottomBar}>
        <div className={styles.summaryText}>
          <Info size={14} color="var(--accent-cyan)" />
          <span>
            Leads in sheet: <strong>{leads.length}</strong> &bull; Click <strong>"Call Phone"</strong> to dial through Twilio directly to your mobile phone.
          </span>
        </div>
        {notification && (
          <div style={{ color: "#10b981", fontSize: "12px", fontWeight: 600, display: "flex", alignItems: "center", gap: "6px" }}>
            <Sparkles size={14} />
            <span>{notification}</span>
          </div>
        )}
      </div>
    </div>
  );
};
