import { NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET() {
  try {
    const response = await fetch(`${backendUrl}/api/v1/dashboard/summary`, {
      cache: "no-store",
    });
    if (!response.ok) {
      return NextResponse.json(
        { detail: "Failed to fetch dashboard summary" },
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
