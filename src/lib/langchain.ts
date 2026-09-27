// Klien server-side untuk backend Python LangChain (FastAPI),
// pengganti langflow.ts (protokol A2A).
//
// Jalur utama: POST {BACKEND}/chat/stream (SSE) -> fallback POST {BACKEND}/chat.
// Jika MOCK_MODE=true (atau backend belum dikonfigurasi), memakai data contoh
// agar UI tetap bisa diuji tanpa backend.

import type { QuickSearch } from "@/lib/types";

const BACKEND_URL =
  process.env.LANGCHAIN_BACKEND_URL ?? "http://127.0.0.1:8000";

const MOCK_MODE =
  process.env.MOCK_MODE === "true" || !BACKEND_URL;

export function isMockMode(): boolean {
  return MOCK_MODE;
}

export interface LangChainStreamResult {
  fullText: string;
  raw?: unknown;
}

type TokenCallback = (token: string) => void;

interface BackendStreamEvent {
  type?: string;
  content?: string;
}

// ============================================================
// Mode LangChain sungguhan (FastAPI SSE -> fallback JSON)
// ============================================================
async function runLangChainLive(params: {
  input: string;
  sessionId: string;
  quickSearch?: QuickSearch;
  signal?: AbortSignal;
  onToken?: TokenCallback;
}): Promise<LangChainStreamResult> {
  const { input, sessionId, quickSearch, signal, onToken } = params;

  const body = JSON.stringify({
    input,
    sessionId,
    quickSearch: quickSearch ?? null,
  });

  const accumulated: string[] = [];
  const pushToken = (t: string) => {
    if (!t) return;
    accumulated.push(t);
    onToken?.(t);
  };

  // 1) Coba jalur streaming SSE
  try {
    const res = await fetch(`${BACKEND_URL.replace(/\/$/, "")}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      signal,
    });
    if (!res.ok) throw new Error(`Backend HTTP ${res.status}`);
    if (!res.body) throw new Error("Backend tidak mengembalikan body stream.");

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() ?? "";

      for (const chunk of chunks) {
        for (const rawLine of chunk.split("\n")) {
          let line = rawLine.trim();
          if (!line) continue;
          if (line.startsWith(":")) continue; // SSE comment / keepalive
          if (line.startsWith("data:")) line = line.slice(5).trim();
          if (!line || line === "[DONE]") continue;

          let ev: BackendStreamEvent;
          try {
            ev = JSON.parse(line);
          } catch {
            continue;
          }
          if (ev.type === "token" && typeof ev.content === "string") {
            pushToken(ev.content);
          } else if (ev.type === "error") {
            throw new Error(ev.content ?? "Backend error");
          }
          // "done" diabaikan di sini — fullText sudah terakumulasi dari token
        }
      }
    }

    if (accumulated.length > 0) {
      return { fullText: accumulated.join(""), raw: { langchain: true } };
    }
    // kalau stream kosong, jatuh ke mode blocking di bawah
  } catch (err) {
    if ((err as Error)?.name === "AbortError") throw err;
    if (accumulated.length > 0) {
      return { fullText: accumulated.join(""), raw: { langchain: true } };
    }
    // lanjut ke fallback blocking
  }

  // 2) Fallback blocking POST /chat (mirip message/send dulu)
  const res = await fetch(`${BACKEND_URL.replace(/\/$/, "")}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
    signal,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Backend HTTP ${res.status}: ${text.slice(0, 300)}`);
  }
  const data = (await res.json()) as { answer?: string };
  const fullText = data.answer ?? "";
  // Simulasikan streaming token agar efek mengetik tetap jalan
  for (const token of fullText.split(/(?<=[ \n])/)) {
    if (signal?.aborted) break;
    pushToken(token);
  }
  return { fullText, raw: { langchain: true } };
}

// ============================================================
// Mode demo (tanpa backend) — reuse mockData yang sama
// ============================================================
async function runLangChainMock(params: {
  input: string;
  quickSearch?: QuickSearch;
  signal?: AbortSignal;
  onToken?: TokenCallback;
}): Promise<LangChainStreamResult> {
  const { input, quickSearch, signal, onToken } = params;

  const answer = await import("@/lib/mockData").then((m) =>
    m.buildMockAnswer(input, quickSearch)
  );

  const delay = (ms: number) =>
    new Promise<void>((resolve) => {
      const timer = setTimeout(resolve, ms);
      if (signal) {
        signal.addEventListener("abort", () => {
          clearTimeout(timer);
          resolve();
        });
      }
    });

  const tokens = answer.fullText.split(/(?<=[ \n])/);
  for (const token of tokens) {
    if (signal?.aborted) break;
    onToken?.(token);
    await delay(16 + Math.random() * 28);
  }

  return { fullText: answer.fullText, raw: { mock: true, perkara: answer.perkara } };
}

export async function runLangChain(params: {
  input: string;
  sessionId: string;
  quickSearch?: QuickSearch;
  signal?: AbortSignal;
  onToken?: TokenCallback;
}): Promise<LangChainStreamResult> {
  if (isMockMode()) {
    return runLangChainMock({
      input: params.input,
      quickSearch: params.quickSearch,
      signal: params.signal,
      onToken: params.onToken,
    });
  }
  return runLangChainLive(params);
}
