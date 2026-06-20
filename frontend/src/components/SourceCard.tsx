import { useMemo, useState } from "react";
import { isProbablyUrl } from "../lib/utils";

type Props = {
  value: string;
};

function formatSourceLabel(value: string): string {
  try {
    const url = new URL(value);
    const path = url.pathname === "/" ? "" : url.pathname;
    return `${url.hostname}${path}`;
  } catch {
    return value;
  }
}

export default function SourceCard({ value }: Props) {
  const [copied, setCopied] = useState(false);
  const isUrl = useMemo(() => isProbablyUrl(value), [value]);
  const label = formatSourceLabel(value);
  const displayLabel = label.length > 92 ? `${label.slice(0, 92)}...` : label;

  async function onClick() {
    if (isUrl) {
      window.open(value, "_blank", "noopener,noreferrer");
      return;
    }

    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1200);
    } catch {
      // ignore
    }
  }

  return (
    <button className="sourceCard" type="button" onClick={onClick}>
      <div className="sourceTop">
        <div className="sourceTitle">{displayLabel}</div>
        <div className="sourceMeta">{isUrl ? "Open" : copied ? "Copied" : "Copy"}</div>
      </div>
      <div className="sourceUrl">{value}</div>
    </button>
  );
}
