import type { ApiError, AskRequest, AskResponse } from "./types";

const DEFAULT_BASE_URL = "http://localhost:8000";

function getBaseUrl(): string {
  const env = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
  return env?.length ? env : DEFAULT_BASE_URL;
}

export async function ask(query: string): Promise<AskResponse> {
  const baseUrl = getBaseUrl();
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 120_000);

  try {
    const payload: AskRequest = { query };
    const res = await fetch(`${baseUrl}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal
    });

    if (!res.ok) {
      let message = `Request failed (${res.status}).`;
      try {
        const body = (await res.json()) as ApiError;
        if (body?.detail) message = body.detail;
      } catch {
        // ignore
      }
      throw new Error(message);
    }

    return (await res.json()) as AskResponse;
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Request timed out.");
    }
    throw err;
  } finally {
    window.clearTimeout(timeout);
  }
}

