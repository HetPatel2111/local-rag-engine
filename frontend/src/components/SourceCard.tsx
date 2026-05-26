import { useMemo, useState } from "react";
import { isProbablyUrl } from "../lib/utils";

type Props = {
  value: string;
};

export default function SourceCard({ value }: Props) {
  const [copied, setCopied] = useState(false);
  const isUrl = useMemo(() => isProbablyUrl(value), [value]);

  const label = value.length > 110 ? `${value.slice(0, 110)}…` : value;

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
    <button className="card sourceCard" type="button" onClick={onClick}>
      <div className="sourceTop">
        <div className="sourceTitle">{label}</div>
        <div className="sourceMeta">{isUrl ? "Open" : copied ? "Copied" : "Copy"}</div>
      </div>
      {isUrl ? <div className="sourceUrl">{value}</div> : null}
    </button>
  );
}

