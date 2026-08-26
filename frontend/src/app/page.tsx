"use client";

import { useEffect, useState } from "react";

type ConnectionState = "checking" | "connected" | "unavailable";

export default function Home() {
  const [connection, setConnection] = useState<ConnectionState>("checking");
  const [service, setService] = useState("agentshield-api");

  useEffect(() => {
    async function checkBackend() {
      try {
        const response = await fetch("/api/backend-health", { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const health = (await response.json()) as { service: string };
        setService(health.service);
        setConnection("connected");
      } catch {
        setConnection("unavailable");
      }
    }

    void checkBackend();
  }, []);

  return (
    <main>
      <section className="hero">
        <p className="eyebrow">AI agent security gateway</p>
        <h1>AgentShield</h1>
        <p className="lede">
          A working foundation for inspecting and securing tool-using AI agent traffic.
        </p>
        <div className={`status status--${connection}`} role="status" aria-live="polite">
          <span className="status__dot" aria-hidden="true" />
          <div>
            <strong>Frontend → Backend</strong>
            <p>
              {connection === "checking" && "Checking connection…"}
              {connection === "connected" && `Connected to ${service}`}
              {connection === "unavailable" && "Backend unavailable"}
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
