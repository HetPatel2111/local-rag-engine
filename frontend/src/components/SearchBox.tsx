import { useEffect, useMemo, useRef } from "react";
import LoadingSpinner from "./LoadingSpinner";

type Props = {
  value: string;
  onChange: (next: string) => void;
  onSubmit: (query: string) => void;
  disabled: boolean;
  canSubmit: boolean;
  submitLabel: string;
};

export default function SearchBox({
  value,
  onChange,
  onSubmit,
  disabled,
  canSubmit,
  submitLabel
}: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const placeholder = useMemo(() => "Ask a question about the indexed docs", []);

  return (
    <form
      className="searchPanel"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(value);
      }}
    >
      <div className="searchField">
        <label className="searchLabel" htmlFor="query">
          Ask a question
        </label>
        <input
          id="query"
          ref={inputRef}
          className="searchInput"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          aria-label="Query"
          spellCheck={false}
        />
      </div>

      <div className="searchActions">
        <button className="primaryButton" type="submit" disabled={!canSubmit}>
          {disabled ? <LoadingSpinner size={16} /> : null}
          <span>{submitLabel}</span>
        </button>
        <div className="searchHint">
          Press Enter to search. Use the example chips for a fast start.
        </div>
      </div>
    </form>
  );
}
