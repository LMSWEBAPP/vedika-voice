"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Megaphone,
  Users,
  PhoneCall,
  Bot,
  BarChart3,
  Settings,
  Radio,
} from "lucide-react";
import styles from "../../styles/layout.module.css";

const navItems = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Campaigns", href: "/campaigns", icon: Megaphone },
  { label: "Leads", href: "/leads", icon: Users },
  { label: "Call History", href: "/calls", icon: PhoneCall },
  { label: "Agent Builder & Live Mic", href: "/agent-builder", icon: Bot },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Settings", href: "/settings", icon: Settings },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className={styles.sidebar}>
      <div className={styles.sidebarBrand}>
        <div className={styles.brandLogo}>V</div>
        <div className={styles.brandTitle}>Veyra Voice</div>
        <span className={styles.brandTag}>AI</span>
      </div>

      <nav className={styles.navSection}>
        <div className={styles.navSectionLabel}>Voice Platform</div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`${styles.navItem} ${isActive ? styles.navItemActive : ""}`}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className={styles.sidebarFooter}>
        <div className={styles.userCard}>
          <div className={styles.userAvatar}>AM</div>
          <div style={{ overflow: "hidden" }}>
            <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--foreground)" }}>Alex Mercer</div>
            <div style={{ fontSize: "11px", color: "var(--foreground-muted)", display: "flex", alignItems: "center", gap: "6px" }}>
              <span className="pulse-indicator" />
              <span>Sim Mode Active</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};
