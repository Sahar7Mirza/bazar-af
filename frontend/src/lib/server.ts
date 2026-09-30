import "server-only";

export const API_URL = process.env.API_URL ?? "http://localhost:8000/api/v1";

/** Server-side fetch of *public* backend endpoints (landing page etc.). Returns null on failure so pages can show an empty state. */
export async function publicGet<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL}/${path}`, { cache: "no-store" });
    return res.ok ? ((await res.json()) as T) : null;
  } catch {
    return null;
  }
}
