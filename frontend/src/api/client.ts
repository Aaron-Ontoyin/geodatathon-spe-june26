import { fetchEventSource } from "@microsoft/fetch-event-source";

import type {
  ChatRequest,
  ConfigResponse,
  Dashboard,
  InputSpec,
  ProgressEvent,
  SearchResultPayload,
  WorkflowPayload,
} from "./types";

// In a production build the API is served same-origin (FastAPI hosts the built UI), so
// default to relative URLs. In dev the Vite server and the API run on separate ports.
const BASE: string =
  import.meta.env.VITE_API_BASE ?? (import.meta.env.DEV ? "http://localhost:8000" : "");

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${detail.slice(0, 300)}`);
  }
  return res.json() as Promise<T>;
}

export const getConfig = (): Promise<ConfigResponse> =>
  fetch(`${BASE}/config`).then((r) => r.json() as Promise<ConfigResponse>);

export const analyze = (spec: InputSpec): Promise<Dashboard> => postJSON("/analyze", spec);

export const getReport = (spec: InputSpec): Promise<{ markdown: string }> =>
  postJSON("/report", spec);

interface StreamHandlers<T> {
  onProgress: (p: ProgressEvent) => void;
  onResult: (result: T) => void;
  onError: (err: unknown) => void;
  signal?: AbortSignal;
}

function streamWithProgress<T>(path: string, body: unknown, h: StreamHandlers<T>): void {
  void fetchEventSource(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: h.signal,
    openWhenHidden: true,
    onmessage(ev) {
      if (!ev.data) return;
      if (ev.event === "progress") h.onProgress(JSON.parse(ev.data) as ProgressEvent);
      else if (ev.event === "result") h.onResult(JSON.parse(ev.data) as T);
    },
    onerror(err) {
      h.onError(err);
      throw err; // stop retrying
    },
  });
}

export const streamOptimize = (spec: InputSpec, h: StreamHandlers<SearchResultPayload>): void =>
  streamWithProgress("/optimize/stream", spec, h);

export const streamWorkflow = (spec: InputSpec, h: StreamHandlers<WorkflowPayload>): void =>
  streamWithProgress("/workflow/stream", spec, h);

export function streamChat(
  req: ChatRequest,
  h: { onToken: (t: string) => void; onDone: () => void; onError: (e: unknown) => void; signal?: AbortSignal },
): void {
  void fetchEventSource(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    signal: h.signal,
    openWhenHidden: true,
    onmessage(ev) {
      if (ev.event === "token") h.onToken(ev.data);
      else if (ev.event === "done") h.onDone();
    },
    onerror(err) {
      h.onError(err);
      throw err;
    },
  });
}
