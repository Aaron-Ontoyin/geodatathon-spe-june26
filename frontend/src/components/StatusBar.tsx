interface StatusBarProps {
  mode: "single" | "optimize";
  onMode: (m: "single" | "optimize") => void;
  onRun: () => void;
  busy: boolean;
  status: string;
}

/** Top status bar: brand, mode toggle, live status readout, and the RUN action. */
export function StatusBar({ mode, onMode, onRun, busy, status }: StatusBarProps) {
  return (
    <div className="statusbar">
      <span className="brand">
        GEOTHERM<span className="dot">.</span>
      </span>
      <span
        className="label"
        style={{ color: "var(--text-dim)", letterSpacing: "0.04em" }}
      >
        Utrecht subsurface instrument
      </span>

      <div className="spacer" style={{ flex: 1 }} />

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

      <div
        className="status-area"
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          minWidth: 0,
        }}
      >
        <span className={busy ? "led busy" : "led"} aria-hidden="true" />
        <span
          className="mono"
          style={{
            color: "var(--text-dim)",
            fontSize: "11px",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {status}
        </span>
      </div>

      <button
        type="button"
        className="btn btn-primary"
        onClick={onRun}
        disabled={busy}
      >
        RUN
        <span className="kbd">⌘↵</span>
      </button>
    </div>
  );
}
