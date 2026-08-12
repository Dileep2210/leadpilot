import type { ExampleLead, HealthStatus, LeadResult, StepEvent } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE || "";

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function fetchExamples(): Promise<ExampleLead[]> {
  const res = await fetch(`${API_BASE}/api/examples`);
  if (!res.ok) throw new Error("Failed to load examples");
  return res.json();
}

interface StreamHandlers {
  onStart: (node: string, label: string) => void;
  onStep: (step: StepEvent) => void;
  onDone: (result: LeadResult) => void;
  onError: (message: string) => void;
}

/**
 * Streams the lead-processing pipeline via Server-Sent Events over a POST
 * request. EventSource doesn't support POST bodies, so we parse the SSE
 * stream manually from a fetch() ReadableStream.
 */
export async function processLeadStream(rawText: string, handlers: StreamHandlers): Promise<void> {
  const res = await fetch(`${API_BASE}/api/process-lead`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_text: rawText }),
  });

  if (!res.ok || !res.body) {
    const detail = await res.text().catch(() => "");
    handlers.onError(`Request failed (${res.status}). ${detail}`.trim());
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";

    for (const rawEvent of events) {
      if (!rawEvent.trim()) continue;
      const lines = rawEvent.split("\n");
      let eventType = "message";
      let data = "";
      for (const line of lines) {
        if (line.startsWith("event: ")) eventType = line.slice(7).trim();
        else if (line.startsWith("data: ")) data += line.slice(6);
      }
      if (!data) continue;
      try {
        const parsed = JSON.parse(data);
        if (eventType === "start") handlers.onStart((parsed as { node: string; label: string }).node, (parsed as { node: string; label: string }).label);
        else if (eventType === "step") handlers.onStep(parsed as StepEvent);
        else if (eventType === "done") handlers.onDone((parsed as { result: LeadResult }).result);
        else if (eventType === "error") handlers.onError((parsed as { message: string }).message);
      } catch {
        // ignore malformed chunk, stream continues
      }
    }
  }
}
