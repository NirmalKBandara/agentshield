import { NextRequest, NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
const allowedPath = /^(?:[0-9a-f-]{36}\/limits|permissions\/[0-9a-f-]{36})$/i;

export async function PATCH(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const suffix = path.join("/");
  if (!allowedPath.test(suffix)) {
    return NextResponse.json({ detail: "Unsupported policy operation" }, { status: 404 });
  }

  try {
    const response = await fetch(`${backendUrl}/api/v1/policies/${suffix}`, {
      method: "PATCH",
      headers: {
        "content-type": "application/json",
        "X-Actor": "dashboard-user",
      },
      body: await request.text(),
      cache: "no-store",
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown backend error";
    return NextResponse.json({ detail: message }, { status: 503 });
  }
}
