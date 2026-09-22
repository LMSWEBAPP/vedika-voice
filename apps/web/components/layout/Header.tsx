"use client";

import React from "react";
import styles from "../../styles/layout.module.css";
import { Sparkles, PhoneIncoming } from "lucide-react";

interface HeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, actions }) => {
  return (
    <header className={styles.header}>
      <div>
        <h1 className={styles.pageTitle}>{title}</h1>
        {subtitle && (
          <p style={{ fontSize: "12px", color: "var(--foreground-muted)", marginTop: "2px" }}>
            {subtitle}
          </p>
        )}
      </div>

      <div className={styles.headerActions}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            background: "rgba(79, 70, 229, 0.12)",
            border: "1px solid rgba(79, 70, 229, 0.25)",
            padding: "5px 12px",
            borderRadius: "var(--radius-full)",
            fontSize: "12px",
            color: "#818cf8",
          }}
        >
          <Sparkles size={14} />
          <span>Gemini Live Ready</span>
        </div>
        {actions}
      </div>
    </header>
  );
};
