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

  const sampleQueries = useMemo(
    () => [
      "What is Vite?",
      "How does HMR work?",
      "What does the config file support?",
      "What is the capital of France?"
    ],
    []
  );

  const canSubmit = query.trim().length > 0 && ui.status !== "loading";

  const headline = useMemo(() => {
    if (ui.status === "loading") return "Searching your local knowledge base";
    if (ui.status === "success") return ui.data.found ? "Grounded answer" : "No strong match";
    if (ui.status === "error") return "Something went wrong";
    return "Ask your knowledge base";
  }, [ui]);

  const subtitle = useMemo(() => {
    if (ui.status === "loading") {
      return "Scanning local chunks, ranking evidence, and assembling a grounded response.";
    }
    if (ui.status === "success") {
      return ui.data.found
        ? "The answer below is built from the strongest local matches and source cards."
        : "The system stayed honest and refused to invent an answer from weak evidence.";
    }
    if (ui.status === "error") {
      return "The backend could not be reached. Check that FastAPI is running on port 8000.";
    }
    return "A local-first RAG interface for fast, grounded answers over your indexed docs.";
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
        <section className="heroGrid">
          <div className="heroPanel">
            <div className="eyebrow">Local-first RAG studio</div>
            <h1 className="title">{headline}</h1>
            <p className="subtitle">{subtitle}</p>

            <div className="statGrid" aria-label="System highlights">
              <div className="statCard">
                <div className="statLabel">Mode</div>
                <div className="statValue">Local</div>
                <div className="statNote">No remote vector service required</div>
              </div>
              <div className="statCard">
                <div className="statLabel">Answering</div>
                <div className="statValue">Grounded</div>
                <div className="statNote">Refuses weak evidence instead of guessing</div>
              </div>
              <div className="statCard">
                <div className="statLabel">Evidence</div>
                <div className="statValue">Sources</div>
                <div className="statNote">Every answer can show the supporting URLs</div>
              </div>
            </div>

            <SearchBox
              value={query}
              onChange={setQuery}
              onSubmit={onSubmit}
              disabled={ui.status === "loading"}
              submitLabel={ui.status === "loading" ? "Searching..." : "Ask"}
              canSubmit={canSubmit}
            />

            <div className="sampleWrap">
              <div className="muted small sampleLabel">Try one of these</div>
              <div className="sampleGrid">
                {sampleQueries.map((sample) => (
                  <button
                    key={sample}
                    type="button"
                    className="sampleButton"
                    onClick={() => {
                      setQuery(sample);
                      void onSubmit(sample);
                    }}
                    disabled={ui.status === "loading"}
                  >
                    {sample}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <aside className="systemPanel">
            <div className="panelHeader">
              <div>
                <div className="sectionTitle">Runtime</div>
                <div className="muted small">What the app is doing right now</div>
              </div>
              <span className="statusPill">{ui.status === "loading" ? "Working" : "Ready"}</span>
            </div>

            <div className="runtimeList">
              <div className="runtimeItem">
                <span className="runtimeKey">Retrieval</span>
                <span className="runtimeValue">Local chunks</span>
              </div>
              <div className="runtimeItem">
                <span className="runtimeKey">Generation</span>
                <span className="runtimeValue">Offline extractive</span>
              </div>
              <div className="runtimeItem">
                <span className="runtimeKey">Backend</span>
                <span className="runtimeValue">FastAPI on :8000</span>
              </div>
              <div className="runtimeItem">
                <span className="runtimeKey">Refusal path</span>
                <span className="runtimeValue">Built in</span>
              </div>
            </div>

            <div className="systemNote">
              This layout is tuned for clarity: strong hero, direct actions, and a response panel
              that explains evidence instead of hiding it.
            </div>
          </aside>
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
