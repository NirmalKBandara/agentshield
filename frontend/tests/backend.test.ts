import { afterEach, describe, expect, it } from "vitest";

import { getBackendHealth } from "../src/lib/backend";

describe("getBackendHealth", () => {
  afterEach(() => {
    delete process.env.BACKEND_URL;
  });

  it("returns FastAPI health data", async () => {
    process.env.BACKEND_URL = "http://backend.test";
    const fetcher = async (input: RequestInfo | URL) => {
      expect(input.toString()).toBe("http://backend.test/api/v1/health");
      return new Response(JSON.stringify({ status: "ok", service: "agentshield-api" }));
    };

    await expect(getBackendHealth(fetcher as typeof fetch)).resolves.toEqual({
      status: "ok",
      service: "agentshield-api",
    });
  });

  it("rejects an unhealthy upstream response", async () => {
    const fetcher = async () => new Response("unavailable", { status: 503 });

    await expect(getBackendHealth(fetcher as typeof fetch)).rejects.toThrow(
      "Backend returned HTTP 503",
    );
  });
});
