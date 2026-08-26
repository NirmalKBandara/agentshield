export type BackendHealth = {
  status: "ok";
  service: string;
};

export async function getBackendHealth(
  fetcher: typeof fetch = fetch,
): Promise<BackendHealth> {
  const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
  const response = await fetcher(`${backendUrl}/api/v1/health`, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
  });

  if (!response.ok) {
    throw new Error(`Backend returned HTTP ${response.status}`);
  }

  return (await response.json()) as BackendHealth;
}
