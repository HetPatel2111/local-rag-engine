import { useMemo, useRef, useState } from "react";
import Navbar from "./components/Navbar";
import SearchBox from "./components/SearchBox";
import AnswerCard from "./components/AnswerCard";
import { ask } from "./lib/api";
import type { AskResponse } from "./lib/types";

type UiState =
  | { status: "idle" }
  | { status: "loading"; query: string }
  | { status: "success"; query: string; data: AskResponse }
  | { status: "error"; query: string; message: string };

export default function App() {
  const [query, setQuery] = useState("");
  const [ui, setUi] = useState<UiState>({ status: "idle" });
  const answerRef = useRef<HTMLDivElement | null>(null);

  const canSubmit = query.trim().length > 0 && ui.status !== "loading";

  const headline = useMemo(() => {
    if (ui.status === "loading") return "Generating answer…";
    if (ui.status === "success") return ui.data.found ? "Answer" : "No strong match";
    if (ui.status === "error") return "Something went wrong";
    return "Ask your knowledge base";
  }, [ui]);

  async function onSubmit(nextQuery: string) {
    const trimmed = nextQuery.trim();
    if (!trimmed) return;
    setUi({ status: "loading", query: trimmed });

    try {
      const data = await ask(trimmed);
      setUi({ status: "success", query: trimmed, data });
      queueMicrotask(() => answerRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Request failed.";
      setUi({ status: "error", query: trimmed, message });
      queueMicrotask(() => answerRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
    }
  }

  return (
    <div className="app">
      <Navbar />

      <main className="container">
        <section className="hero">
          <h1 className="title">{headline}</h1>
          <p className="subtitle">
            A minimal, professional RAG UI connected to your local FastAPI backend.
          </p>
          <SearchBox
            value={query}
            onChange={setQuery}
            onSubmit={onSubmit}
            disabled={ui.status === "loading"}
            submitLabel={ui.status === "loading" ? "Searching…" : "Ask"}
            canSubmit={canSubmit}
          />
        </section>

        <section className="results" ref={answerRef}>
          <AnswerCard ui={ui} onRetry={() => onSubmit(ui.status === "idle" ? query : ui.query)} />
        </section>
      </main>

      <footer className="footer">
        <div className="footerInner">
          <span className="muted">Local API:</span>
          <code className="pill">{import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"}</code>
        </div>
      </footer>
    </div>
  );
}

