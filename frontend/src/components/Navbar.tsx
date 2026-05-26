import { useEffect } from "react";
import { useLocalStorage } from "../hooks/useLocalStorage";

type Theme = "dark" | "light";

export default function Navbar() {
  const [theme, setTheme] = useLocalStorage<Theme>("rag_theme", "dark");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  return (
    <header className="nav">
      <div className="navInner">
        <div className="brand">
          <div className="brandMark" aria-hidden="true" />
          <div className="brandText">
            <div className="brandName">Semantic Docs RAG</div>
            <div className="brandSub">FastAPI • Gemini • Chroma</div>
          </div>
        </div>

        <button
          className="iconButton"
          type="button"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          {theme === "dark" ? (
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
              <path
                fill="currentColor"
                d="M12 18a6 6 0 1 1 0-12a6 6 0 0 1 0 12Zm0-16a1 1 0 0 1 1 1v1a1 1 0 1 1-2 0V3a1 1 0 0 1 1-1Zm0 18a1 1 0 0 1 1 1v1a1 1 0 1 1-2 0v-1a1 1 0 0 1 1-1ZM3 11a1 1 0 0 1 1 1a1 1 0 1 1-2 0a1 1 0 0 1 1-1Zm18 0a1 1 0 0 1 1 1a1 1 0 1 1-2 0a1 1 0 0 1 1-1ZM5.6 5.6a1 1 0 0 1 1.4 0l.7.7a1 1 0 1 1-1.4 1.4l-.7-.7a1 1 0 0 1 0-1.4Zm12.7 12.7a1 1 0 0 1 1.4 0l.7.7a1 1 0 1 1-1.4 1.4l-.7-.7a1 1 0 0 1 0-1.4ZM18.4 5.6a1 1 0 0 1 0 1.4l-.7.7a1 1 0 0 1-1.4-1.4l.7-.7a1 1 0 0 1 1.4 0ZM6.3 16.3a1 1 0 0 1 0 1.4l-.7.7a1 1 0 1 1-1.4-1.4l.7-.7a1 1 0 0 1 1.4 0Z"
              />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
              <path
                fill="currentColor"
                d="M21 14.5A8.5 8.5 0 0 1 9.5 3a7 7 0 1 0 11.5 11.5Z"
              />
            </svg>
          )}
        </button>
      </div>
    </header>
  );
}

