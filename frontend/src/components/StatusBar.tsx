interface StatusBarProps {
  mode: "single" | "optimize";
  onMode: (m: "single" | "optimize") => void;
  onRun: () => void;
  busy: boolean;
  status: string;
}

/** Top navigation bar: brand, mode toggle, live status readout, and the RUN action.
    Grid areas reflow to a two-row layout on narrow screens. */
export function StatusBar({ mode, onMode, onRun, busy, status }: StatusBarProps) {
  return (
    <header className="statusbar">
      <div className="sb-brand">
        <span className="brand">
          GEOTHERM<span className="dot">.</span>
        </span>
        <span className="sb-subtitle label">Utrecht subsurface instrument</span>
      </div>

      <div className="sb-controls">
        <div className="seg" role="group" aria-label="Run mode">
          <button
            type="button"
            className={mode === "single" ? "active" : ""}
            onClick={() => onMode("single")}
          >
            EVALUATE
          </button>
          <button
            type="button"
            className={mode === "optimize" ? "active" : ""}
            onClick={() => onMode("optimize")}
          >
            OPTIMISE
          </button>
        </div>

        <div className="status-area">
          <span className={busy ? "led busy" : "led"} aria-hidden="true" />
          <span className="mono sb-status">{status}</span>
        </div>
      </div>

      <button type="button" className="btn btn-primary sb-run" onClick={onRun} disabled={busy}>
        RUN
        <span className="kbd">⌘↵</span>
      </button>
    </header>
  );
}
