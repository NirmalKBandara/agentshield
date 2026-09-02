"use client";

import Link from "next/link";

export default function Home() {
  return (
    <main style={{ padding: "2rem" }}>
      <header style={{ marginBottom: "3rem" }}>
        <h1 style={{ fontSize: "3rem", marginBottom: "0.5rem" }}>AgentShield</h1>
        <p style={{ fontSize: "1.25rem", color: "#666" }}>
          AI Agent Security Gateway
        </p>
      </header>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Welcome to AgentShield</h2>
        <p>
          AgentShield is a security gateway that protects tool-using AI agents from unsafe actions
          and adversarial inputs. This demo application shows how security controls can intercept,
          analyze, and block dangerous tool requests before they execute.
        </p>
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Available Pages</h2>
        <nav style={{ display: "grid", gap: "1rem" }}>
          <Link
            href="/playground"
            style={{
              padding: "1rem",
              backgroundColor: "#e3f2fd",
              borderRadius: "0.5rem",
              textDecoration: "none",
              color: "#1976d2",
              fontWeight: "bold",
            }}
          >
            → Agent Playground - Try the AI agent with different prompts
          </Link>
          <Link
            href="/dashboard"
            style={{
              padding: "1rem",
              backgroundColor: "#e8f5e9",
              borderRadius: "0.5rem",
              textDecoration: "none",
              color: "#388e3c",
              fontWeight: "bold",
            }}
          >
            → Dashboard - View security metrics and recent events
          </Link>
          <Link
            href="/security-events"
            style={{
              padding: "1rem",
              backgroundColor: "#fff3e0",
              borderRadius: "0.5rem",
              textDecoration: "none",
              color: "#f57c00",
              fontWeight: "bold",
            }}
          >
            → Security Events - Inspect blocked actions and threats
          </Link>
          <Link
            href="/tool-calls"
            style={{
              padding: "1rem",
              backgroundColor: "#f3e5f5",
              borderRadius: "0.5rem",
              textDecoration: "none",
              color: "#7b1fa2",
              fontWeight: "bold",
            }}
          >
            → Tool Calls - Audit all tool execution attempts
          </Link>
          <Link
            href="/policies"
            style={{
              padding: "1rem",
              backgroundColor: "#e0f2f1",
              borderRadius: "0.5rem",
              textDecoration: "none",
              color: "#00796b",
              fontWeight: "bold",
            }}
          >
            → Policies - Manage tool permissions and runtime limits
          </Link>
          <Link
            href="/red-team"
            style={{
              padding: "1rem",
              backgroundColor: "#ffebee",
              borderRadius: "0.5rem",
              textDecoration: "none",
              color: "#b4233c",
              fontWeight: "bold",
            }}
          >
            → Red Team Lab - Reproduce six safe attack simulations
          </Link>
        </nav>
      </section>

      <section>
        <h2>Demo Features</h2>
        <ul>
          <li>AI agent using structured tool calling</li>
          <li>Four demo tools: get_customer, send_email, issue_refund, fetch_url</li>
          <li>Tool permission validation</li>
          <li>Security event logging and audit trail</li>
          <li>Dashboard with security metrics</li>
        </ul>
      </section>
    </main>
  );
}
