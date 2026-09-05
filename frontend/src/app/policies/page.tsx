"use client";

import { FormEvent, useEffect, useState } from "react";

import {
  describeAudit,
  type PolicyOverview,
  validatePolicyValues,
} from "@/lib/policies";

const controlStyle = {
  width: "100%",
  padding: ".65rem",
  color: "var(--ink)",
  border: "1px solid var(--line)",
  borderRadius: ".45rem",
  background: "var(--panel)",
};

function errorDetail(payload: unknown, fallback: string): string {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}

async function fetchOverview(): Promise<PolicyOverview> {
  const response = await fetch("/api/policies", { cache: "no-store" });
  const payload = (await response.json()) as PolicyOverview | { detail?: unknown };
  if (!response.ok) throw new Error(errorDetail(payload, "Failed to load policies"));
  return payload as PolicyOverview;
}

export default function PoliciesPage() {
  const [overview, setOverview] = useState<PolicyOverview | null>(null);
  const [refundLimit, setRefundLimit] = useState("");
  const [rateLimit, setRateLimit] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState("");
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [success, setSuccess] = useState("");

  useEffect(() => {
    async function initialize() {
      setLoading(true);
      setError("");
      try {
        const data = await fetchOverview();
        setOverview(data);
        if (data.policies[0]) {
          setRefundLimit(String(data.policies[0].refund_limit));
          setRateLimit(String(data.policies[0].rate_limit_per_minute));
        }
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Failed to load policies");
      } finally {
        setLoading(false);
      }
    }
    void initialize();
  }, [refresh]);

  async function reloadOverview() {
    const data = await fetchOverview();
    setOverview(data);
    if (data.policies[0]) {
      setRefundLimit(String(data.policies[0].refund_limit));
      setRateLimit(String(data.policies[0].rate_limit_per_minute));
    }
  }

  async function updateLimits(event: FormEvent) {
    event.preventDefault();
    const policy = overview?.policies[0];
    if (!policy) return;
    const refund = Number(refundLimit);
    const rate = Number(rateLimit);
    const validationErrors = validatePolicyValues(refund, rate);
    if (validationErrors.length) {
      setError(validationErrors.join(" "));
      setSuccess("");
      return;
    }

    setSaving("limits");
    setError("");
    setSuccess("");
    try {
      const response = await fetch(`/api/policies/${policy.id}/limits`, {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ refund_limit: refund, rate_limit_per_minute: rate }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(errorDetail(payload, "Failed to update limits"));
      await reloadOverview();
      setSuccess("Runtime policy limits saved and audited.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to update limits");
    } finally {
      setSaving("");
    }
  }

  async function togglePermission(permissionId: string, allowed: boolean) {
    setSaving(permissionId);
    setError("");
    setSuccess("");
    try {
      const response = await fetch(`/api/policies/permissions/${permissionId}`, {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ allowed }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(errorDetail(payload, "Failed to update permission"));
      await reloadOverview();
      setSuccess("Tool permission saved and audited.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to update permission");
    } finally {
      setSaving("");
    }
  }

  return (
    <main id="main-content" className="app-main" tabIndex={-1}>
      <header style={{ marginBottom: "2rem" }}>
        <h1>Security Policies</h1>
        <p style={{ color: "var(--muted)", maxWidth: "48rem", lineHeight: 1.6 }}>
          Manage the demo agent&apos;s least-privilege tool access and runtime safety limits.
        </p>
      </header>

      {error && <div className="error" role="alert"><strong>Security Policies unavailable or update failed</strong><p>{error}</p><button className="secondary-button" disabled={loading} onClick={() => setRefresh((value) => value + 1)}>Retry loading</button></div>}
      {success && <p role="status" style={{ padding: "1rem", border: "1px solid var(--accent)", borderRadius: ".6rem" }}>{success}</p>}

      {loading ? (
        <p aria-live="polite" style={{ color: "var(--muted)" }}>Loading policies…</p>
      ) : error && !overview ? null : !overview || overview.policies.length === 0 ? (
        <p style={{ color: "var(--muted)" }}>No configurable policies are available. Run the latest database migration.</p>
      ) : (
        <>
          <section style={{ marginBottom: "3rem" }} aria-labelledby="runtime-limits">
            <h2 id="runtime-limits" style={{ fontSize: "2.4rem", marginBottom: ".5rem" }}>Runtime limits</h2>
            <p style={{ color: "var(--muted)" }}>{overview.policies[0].description}</p>
            <form onSubmit={updateLimits} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 14rem), 1fr))", gap: "1rem", maxWidth: "48rem", alignItems: "end" }}>
              <label>
                <span style={{ display: "block", marginBottom: ".4rem" }}>Maximum refund amount</span>
                <input aria-describedby="refund-help" type="number" min="0.01" max="10000" step="0.01" value={refundLimit} onChange={(event) => setRefundLimit(event.target.value)} style={controlStyle} />
                <small id="refund-help" style={{ color: "var(--muted)" }}>Blocks larger refund requests.</small>
              </label>
              <label>
                <span style={{ display: "block", marginBottom: ".4rem" }}>Requests per minute</span>
                <input aria-describedby="rate-help" type="number" min="1" max="1000" step="1" value={rateLimit} onChange={(event) => setRateLimit(event.target.value)} style={controlStyle} />
                <small id="rate-help" style={{ color: "var(--muted)" }}>Applied per agent in this app instance.</small>
              </label>
              <button type="submit" disabled={saving !== ""} style={{ ...controlStyle, cursor: "pointer", fontWeight: 700 }}>
                {saving === "limits" ? "Saving…" : "Save limits"}
              </button>
            </form>
          </section>

          <section style={{ marginBottom: "3rem" }} aria-labelledby="tool-permissions">
            <h2 id="tool-permissions" style={{ fontSize: "2.4rem", marginBottom: ".5rem" }}>Tool permissions</h2>
            <p style={{ color: "var(--muted)" }}>Changes take effect on the next agent request. Unlisted permissions remain denied.</p>
            <div style={{ display: "grid", gap: ".65rem", maxWidth: "48rem" }}>
              {overview.permissions.map((permission) => (
                <label key={permission.id} style={{ display: "flex", justifyContent: "space-between", gap: "1rem", padding: "1rem", border: "1px solid var(--line)", borderRadius: ".6rem", background: "var(--panel)" }}>
                  <span><strong><code>{permission.tool_name}</code></strong><br /><small style={{ color: "var(--muted)" }}>{permission.agent_name}</small></span>
                  <span style={{ display: "flex", alignItems: "center", gap: ".55rem" }}>
                    {permission.allowed ? "Allowed" : "Blocked"}
                    <input type="checkbox" checked={permission.allowed} disabled={saving !== ""} onChange={(event) => void togglePermission(permission.id, event.target.checked)} aria-label={`${permission.tool_name} allowed`} />
                  </span>
                </label>
              ))}
            </div>
          </section>

          <section aria-labelledby="policy-audit">
            <h2 id="policy-audit" style={{ fontSize: "2.4rem", marginBottom: ".5rem" }}>Recent changes</h2>
            {overview.recent_changes.length === 0 ? (
              <p style={{ color: "var(--muted)" }}>No policy changes have been recorded.</p>
            ) : (
              <ul style={{ padding: 0, listStyle: "none", maxWidth: "48rem" }}>
                {overview.recent_changes.map((change) => (
                  <li key={change.id} style={{ padding: ".85rem 0", borderBottom: "1px solid var(--line)" }}>
                    <strong>{describeAudit(change)}</strong> by {change.actor}
                    <br /><small style={{ color: "var(--muted)" }}>{new Date(change.created_at).toLocaleString()} · Request {change.request_id}</small>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </main>
  );
}
