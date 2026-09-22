"use client";

import React from "react";
import { Sidebar } from "./Sidebar";
import styles from "../../styles/layout.module.css";

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  return (
    <div className={styles.layoutWrapper}>
      <Sidebar />
      <div className={styles.mainArea}>{children}</div>
    </div>
  );
};
