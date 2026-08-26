import { NextResponse } from "next/server";

import { getBackendHealth } from "@/lib/backend";

export async function GET() {
  try {
    const health = await getBackendHealth();
    return NextResponse.json(health);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown backend error";
    return NextResponse.json(
      { status: "error", service: "agentshield-api", message },
      { status: 503 },
    );
  }
}
