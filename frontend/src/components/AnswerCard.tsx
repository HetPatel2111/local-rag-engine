import SourceCard from "./SourceCard";
import { clamp01, formatMs } from "../lib/utils";
import type { AskResponse } from "../lib/types";

type UiState =
  | { status: "idle" }
  | { status: "loading"; query: string }
  | { status: "success"; query: string; data: AskResponse }
  | { status: "error"; query: string; message: string };

type Props = {
  ui: UiState;
  onRetry: () => void;
};

function Skeleton() {
  return (
    <div className="responseCard shimmer">
      <div className="row">
        <div>
          <div className="skeleton skTitle" />
          <div className="skeleton skText short" />
        </div>
        <div className="skeleton skPill" />
      </div>
      <div className="skeleton skAnswer" />
      <div className="skeleton skAnswer short" />
      <div className="skeleton skAnswer tiny" />
      <div className="divider" />
      <div className="grid">
        <div className="skeleton skCard" />
        <div className="skeleton skCard" />
      </div>
    </div>
  );
}

export default function AnswerCard({ ui, onRetry }: Props) {
  if (ui.status === "idle") {
    return (
      <div className="responseCard emptyState">
        <div className="emptyBadge">Ready</div>
        <h2 className="emptyTitle">Your answer will appear here.</h2>
        <p className="emptyBody">
          Ask a docs question, then inspect the evidence, confidence, and sources that support the answer.
        </p>
        <div className="emptyTips">
          <span className="pill">Try "What is Vite?"</span>
          <span className="pill">Try "How does HMR work?"</span>
        </div>
      </div>
    );
  }

  if (ui.status === "loading") {
    return (
      <>
        <div className="callout">
          <div className="calloutDot" />
          <div>
            <div className="calloutTitle">Searching local evidence</div>
            <div className="calloutSub">Query: "{ui.query}"</div>
          </div>
        </div>
        <Skeleton />
      </>
    );
  }

  if (ui.status === "error") {
    return (
      <div className="responseCard">
        <div className="panelHeader">
          <div>
            <div className="cardTitle">Connection problem</div>
            <div className="muted">Query: "{ui.query}"</div>
          </div>
          <button className="secondaryButton" type="button" onClick={onRetry}>
            Retry
          </button>
        </div>
        <div className="errorBox">{ui.message}</div>
        <div className="muted small">
          Check that the FastAPI server is running at{" "}
          <code>{import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"}</code>.
        </div>
      </div>
    );
  }

  const data = ui.data;
  const confidence = clamp01(data.confidence);
  const confidenceLabel = data.found ? "Grounded" : "Weak match";

  return (
    <div className="responseCard">
      <div className="panelHeader">
        <div>
          <div className="eyebrow">Answer</div>
          <div className="cardTitle">{data.found ? "Grounded answer" : "No strong match"}</div>
          <div className="muted">Query: "{data.query}"</div>
        </div>
        <div className="pillGroup">
          <span className="pill">
            <span className="muted">Model</span> {data.model || "Unknown"}
          </span>
          <span className="pill">
            <span className="muted">Latency</span> {formatMs(data.latency_ms)}
          </span>
          <span className="pill">
            <span className="muted">Status</span> {confidenceLabel}
          </span>
        </div>
      </div>

      <div className="answerBlock">{data.answer || "No answer returned."}</div>

      <div className="metricsGrid">
        <div className="metricCard">
          <div className="metricLabel">Confidence</div>
          <div className="metricValue">{Math.round(confidence * 100)}%</div>
          <div className="progress" aria-label="Confidence">
            <div className="progressFill" style={{ width: `${confidence * 100}%` }} />
          </div>
        </div>
        <div className="metricCard">
          <div className="metricLabel">Sources</div>
          <div className="metricValue">{data.sources?.length ?? 0}</div>
          <div className="metricNote">Supporting URLs returned with the answer</div>
        </div>
        <div className="metricCard">
          <div className="metricLabel">Finish</div>
          <div className="metricValue">{data.finish_reason || "N/A"}</div>
          <div className="metricNote">Generation metadata or offline fallback status</div>
        </div>
      </div>

      <div className="divider" />

      <div className="panelHeader">
        <div>
          <div className="sectionTitle">Sources</div>
          <div className="muted small">{data.sources?.length ?? 0} item(s)</div>
        </div>
      </div>
      {data.sources?.length ? (
        <div className="grid">
          {data.sources.map((s, idx) => (
            <SourceCard key={`${idx}-${s}`} value={s} />
          ))}
        </div>
      ) : (
        <div className="muted">No sources returned.</div>
      )}
    </div>
  );
}
