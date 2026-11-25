import { env } from "@/shared/lib/env";
import { useSession } from "@/features/auth/session";
import { problemSchema, type Problem } from "./schemas";

export class ApiError extends Error {
  readonly problem: Problem;
  constructor(problem: Problem) {
    super(problem.detail ?? problem.title);
    this.problem = problem;
  }
}

function newIdempotencyKey(): string {
  return crypto.randomUUID();
}

let refreshInFlight: Promise<boolean> | null = null;

async function parseProblem(res: Response): Promise<Problem> {
  try {
    const json: unknown = await res.json();
    const parsed = problemSchema.safeParse(json);
    if (parsed.success) return parsed.data;
  } catch {
    /* ignore */
  }
  return {
    type: "https://mindgenome.ai/problems/unknown",
    title: res.statusText || "Request failed",
    status: res.status,
    detail: "The server returned an unexpected error.",
  };
}

async function tryRefresh(): Promise<boolean> {
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = (async () => {
    const refresh = useSession.getState().refreshToken;
    if (!refresh && !env.authCookie) return false;
    const res = await fetch(`${env.apiBaseUrl}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: env.authCookie ? "include" : "same-origin",
      body: JSON.stringify({ refresh_token: refresh ?? "" }),
    });
    if (!res.ok) {
      useSession.getState().clear();
      return false;
    }
    const body = (await res.json()) as {
      access_token: string;
      refresh_token: string;
      expires_in: number;
    };
    useSession.getState().setTokens(body.access_token, body.refresh_token, body.expires_in);
    return true;
  })();
  try {
    return await refreshInFlight;
  } finally {
    refreshInFlight = null;
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit & { idempotent?: boolean } = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  const access = useSession.getState().accessToken;
  if (access) headers.set("Authorization", `Bearer ${access}`);
  if (init.idempotent && !headers.has("Idempotency-Key")) {
    headers.set("Idempotency-Key", newIdempotencyKey());
  }
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const doFetch = () =>
    fetch(`${env.apiBaseUrl}${path}`, {
      ...init,
      headers,
      credentials: env.authCookie ? "include" : "same-origin",
    });

  let res = await doFetch();
  if (res.status === 401 && !path.startsWith("/auth/")) {
    const ok = await tryRefresh();
    if (ok) {
      const next = new Headers(headers);
      const token = useSession.getState().accessToken;
      if (token) next.set("Authorization", `Bearer ${token}`);
      res = await fetch(`${env.apiBaseUrl}${path}`, { ...init, headers: next });
    }
  }
  if (!res.ok) throw new ApiError(await parseProblem(res));
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
