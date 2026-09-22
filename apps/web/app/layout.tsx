import "../styles/globals.css";
import "../styles/components.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Veyra Voice - AI Outbound Voice Calling Platform",
  description: "Enterprise AI outbound voice calling platform powered by Gemini Live and carrier telephony",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
