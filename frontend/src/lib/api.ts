export interface FieldError { field: string; message: string }
export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public details?: FieldError[], public requestId?: string) { super(message); }
}

/** Browser-side client. Calls go through the Next.js BFF (/api/proxy), which attaches the httpOnly token cookie. */
export async function api<T = unknown>(path: string, init: { method?: string; body?: unknown; query?: Record<string, string | number | undefined | null> } = {}): Promise<T> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(init.query ?? {})) if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  const url = `/api/proxy/${path.replace(/^\//, "")}${qs.size ? `?${qs}` : ""}`;
  let res: Response;
  try {
    res = await fetch(url, { method: init.method ?? "GET", headers: init.body !== undefined ? { "Content-Type": "application/json" } : undefined, body: init.body !== undefined ? JSON.stringify(init.body) : undefined });
  } catch {
    throw new ApiError(0, "network", "Cannot reach the server. Check your connection and try again.");
  }
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const e = data?.error;
    throw new ApiError(res.status, e?.code ?? "error", e?.message ?? "Something went wrong", e?.details, e?.request_id);
  }
  return data as T;
}

export function fieldErrors(err: unknown): Record<string, string> {
  const out: Record<string, string> = {};
  if (err instanceof ApiError) for (const d of err.details ?? []) if (d.field) out[d.field] = d.message;
  return out;
}
