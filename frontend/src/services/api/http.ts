import { RuleError } from "../types";

const API_BASE = (import.meta.env["VITE_API_BASE_URL"] as string | undefined) ?? "";
const TOKEN_KEY = "family-kanban-token";

export function getAccessToken(): string | null {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token: string | null): void {
  if (typeof localStorage === "undefined") return;
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export async function api<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = {};
  const token = getAccessToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const init: RequestInit = { method, headers };
  if (body !== undefined) init.body = JSON.stringify(body);

  const res = await fetch(`${API_BASE}/api/v1${path}`, init);

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  // Empty body or JSON `null` (e.g. GET /auth/session when signed out) → null
  const data = text ? (JSON.parse(text) as unknown) : null;

  if (!res.ok) {
    const message =
      data &&
      typeof data === "object" &&
      "message" in data &&
      typeof (data as { message: unknown }).message === "string"
        ? (data as { message: string }).message
        : res.statusText || "Request failed";
    throw new RuleError(message);
  }

  return data as T;
}
