import { NextRequest, NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const query = new URLSearchParams();

    for (const name of [
      "severity",
      "event_type",
      "tool",
      "decision",
      "min_risk_score",
      "tool_call_id",
      "limit",
      "offset",
    ]) {
      const value = searchParams.get(name);
      if (value !== null) query.set(name, value);
    }

    const suffix = query.size > 0 ? `?${query.toString()}` : "";
    const url = `${backendUrl}/api/v1/security-events${suffix}`;
    const response = await fetch(url, { cache: "no-store" });

    if (!response.ok) {
      return NextResponse.json(
        { detail: "Failed to fetch security events" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown backend error";
    return NextResponse.json({ detail: message }, { status: 503 });
  }
}
