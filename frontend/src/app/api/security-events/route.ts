import { NextRequest, NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const query = new URLSearchParams();

    if (searchParams.has("severity")) {
      query.set("severity", searchParams.get("severity")!);
    }
    if (searchParams.has("limit")) {
      query.set("limit", searchParams.get("limit")!);
    }

    const url = `${backendUrl}/api/v1/security-events?${query.toString()}`;
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
