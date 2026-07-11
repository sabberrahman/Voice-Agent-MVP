export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function getToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("voxagent_token");
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export async function login(email: string, password: string) {
  return apiFetch<{ access_token: string; role: string; user: Record<string, string> }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}
