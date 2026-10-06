"use client";

import React from "react";
import { AppLayout } from "../../components/layout/AppLayout";
import { Header } from "../../components/layout/Header";
import { VoiceAgentView } from "../../features/voice-agent/components/VoiceAgentView";

export default function AskVedikaPage() {
  return (
    <AppLayout>
      <Header
        title="Live Outbound Voice Studio — B2B Software Pitching"
        subtitle="Sub-second full-duplex conversational voice pitching powered by Google Gemini Multimodal Live API"
      />
      <main style={{ padding: "24px 32px", maxWidth: "1600px", margin: "0 auto" }}>
        <VoiceAgentView inline={false} />
      </main>
    </AppLayout>
  );
}
