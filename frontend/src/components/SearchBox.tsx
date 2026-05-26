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

  const placeholder = useMemo(
    () => "Ask a question (e.g., “What is our leave policy?”)",
    []
  );

  return (
    <form
      className="search"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(value);
      }}
    >
      <div className="searchField">
        <input
          ref={inputRef}
          className="searchInput"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          aria-label="Query"
        />
      </div>

      <button className="primaryButton" type="submit" disabled={!canSubmit}>
        {disabled ? <LoadingSpinner size={16} /> : null}
        <span>{submitLabel}</span>
      </button>
    </form>
  );
}

