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
    <div className="card fadeIn">
      <div className="row">
        <div className="skeleton skTitle" />
        <div className="skeleton skPill" />
      </div>
      <div className="skeleton skLine" />
      <div className="skeleton skLine" />
      <div className="skeleton skLine short" />
      <div className="divider" />
      <div className="row">
        <div className="skeleton skLabel" />
        <div className="skeleton skLabel" />
      </div>
      <div className="skeleton skBar" />
      <div className="divider" />
      <div className="row">
        <div className="skeleton skLabel" />
        <div className="skeleton skLabel" />
      </div>
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
      <div className="card subtle">
        <div className="muted">Tip</div>
        <div className="body">Press Enter to submit. Results will appear here.</div>
      </div>
    );
  }

  if (ui.status === "loading") {
    return (
      <>
        <div className="callout fadeIn">
          <div className="calloutDot" />
          <div>
            <div className="calloutTitle">Generating answer…</div>
            <div className="calloutSub">Query: “{ui.query}”</div>
          </div>
        </div>
        <Skeleton />
      </>
    );
  }

  if (ui.status === "error") {
    return (
      <div className="card fadeIn">
        <div className="row">
          <div>
            <div className="cardTitle">Error</div>
            <div className="muted">Query: “{ui.query}”</div>
          </div>
          <button className="secondaryButton" type="button" onClick={onRetry}>
            Retry
          </button>
        </div>
        <div className="errorBox">{ui.message}</div>
        <div className="muted small">
          Make sure your FastAPI server is running and reachable at{" "}
          <code>{import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"}</code>.
        </div>
      </div>
    );
  }

  const data = ui.data;
  const confidence = clamp01(data.confidence);

  return (
    <div className="card fadeIn">
      <div className="row">
        <div>
          <div className="cardTitle">Answer</div>
          <div className="muted">Query: “{data.query}”</div>
        </div>
        <div className="pillGroup">
          <span className="pill">
            <span className="muted">Model:</span> {data.model || "—"}
          </span>
          <span className="pill">
            <span className="muted">Latency:</span> {formatMs(data.latency_ms)}
          </span>
        </div>
      </div>

      <div className="divider" />

      <div className="answerText">{data.answer || "—"}</div>

      <div className="divider" />

      <div className="row">
        <div className="sectionTitle">Confidence</div>
        <div className="muted">{Math.round(confidence * 100)}%</div>
      </div>
      <div className="progress" aria-label="Confidence">
        <div className="progressFill" style={{ width: `${confidence * 100}%` }} />
      </div>

      <div className="divider" />

      <div className="row">
        <div className="sectionTitle">Sources</div>
        <div className="muted small">{data.sources?.length ?? 0}</div>
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

