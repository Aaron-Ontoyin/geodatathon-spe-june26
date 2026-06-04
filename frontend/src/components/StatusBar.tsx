import { Tooltip } from "./Tooltip";

interface StatusBarProps {
  mode: "single" | "optimize";
  onMode: (m: "single" | "optimize") => void;
  onRun: () => void;
  busy: boolean;
  status: string;
  onClear: () => void;
  hasResult: boolean;
}

/** Top navigation bar: brand, mode toggle, live status readout, and the run actions.
    Grid areas reflow to a two-row layout on narrow screens. */
export function StatusBar({ mode, onMode, onRun, busy, status, onClear, hasResult }: StatusBarProps) {
  return (
    <header className="statusbar">
      <div className="sb-brand">
        <span className="brand">GEOTHERM</span>
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
                <strong>Evaluate</strong>: design &amp; LCoE for your exact inputs.
                <br />
                <strong>Optimise</strong>: search the parameters you mark as ranges for the
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

      <div className="sb-actions">
        {hasResult && (
          <button type="button" className="btn" onClick={onClear} disabled={busy}>
            CLEAR
          </button>
        )}
        <button type="button" className="btn btn-primary" onClick={onRun} disabled={busy}>
          RUN
          <span className="kbd">⌘↵</span>
        </button>
      </div>
    </header>
  );
}
