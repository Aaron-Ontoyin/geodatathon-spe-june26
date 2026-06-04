import { Tooltip } from "./Tooltip";

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
        <div className="seg-help">
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
          <Tooltip
            side="bottom"
            label={
              <>
                <strong>Evaluate</strong> — design &amp; LCoE for your exact inputs.
                <br />
                <strong>Optimise</strong> — search the parameters you mark as ranges for the
                least-cost design.
              </>
            }
          >
            <button
              type="button"
              className="help-badge"
              aria-label="What do Evaluate and Optimise mean?"
            >
              ?
            </button>
          </Tooltip>
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
