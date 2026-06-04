import { useCallback, useEffect, useMemo, useState } from "react";

import { analyze, getConfig, getReport, streamOptimize } from "./api/client";
import type { Assumptions, ConfigResponse, Dashboard, InputSpec, ProgressEvent } from "./api/types";
import { ChatDock } from "./components/ChatDock";
import { ComparisonTable } from "./components/ComparisonTable";
import { DecisionLog } from "./components/DecisionLog";
import { DispatchChart } from "./components/DispatchChart";
import { HeadlineStrip } from "./components/HeadlineStrip";
import { InputsPanel, type SearchState } from "./components/InputsPanel";
import { MonteCarloChart } from "./components/MonteCarloChart";
import { PercentilesChart } from "./components/PercentilesChart";
import { ReportPanel } from "./components/ReportPanel";
import { ResourceMap } from "./components/ResourceMap";
import { StatusBar } from "./components/StatusBar";
import { Tooltip } from "./components/Tooltip";
import { TornadoChart } from "./components/TornadoChart";
import { useResizable } from "./hooks/useResizable";
import { useShortcuts } from "./hooks/useShortcuts";

const INITIAL_SEARCH: SearchState = { ranges: {}, constraints: {}, objective: "min_lcoe" };

export function App() {
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [values, setValues] = useState<Assumptions>({});
  const [mode, setMode] = useState<"single" | "optimize">("single");
  const [search, setSearch] = useState<SearchState>(INITIAL_SEARCH);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [reportMd, setReportMd] = useState<string | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState<ProgressEvent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showKeys, setShowKeys] = useState(false);
  const rail = useResizable({ storageKey: "geotherm.rail-width", initial: 420, min: 300, max: 640 });

  useEffect(() => {
    getConfig()
      .then((c) => {
        setConfig(c);
        setValues(c.defaults);
      })
      .catch((e) => setError(String(e)));
  }, []);

  const buildSpec = useCallback((): InputSpec => {
    const spec: InputSpec = { assumptions: values };
    if (mode === "optimize") {
      const constraints: Record<string, number> = {};
      if (search.constraints.max_capex_meur != null)
        constraints.max_capex_meur = search.constraints.max_capex_meur;
      if (search.constraints.max_lcoe_eur_per_gj != null)
        constraints.max_lcoe_eur_per_gj = search.constraints.max_lcoe_eur_per_gj;
      spec.search = { ranges: search.ranges, constraints, objective: search.objective };
    }
    return spec;
  }, [values, mode, search]);

  const loadReport = useCallback((spec: InputSpec) => {
    setReportMd(null);
    setReportLoading(true);
    getReport(spec)
      .then((r) => setReportMd(r.markdown))
      .catch(() => setReportMd(null))
      .finally(() => setReportLoading(false));
  }, []);

  const run = useCallback(() => {
    if (busy || !config) return;
    setError(null);
    setBusy(true);
    setProgress(null);
    const spec = buildSpec();
    if (mode === "single") {
      analyze(spec)
        .then((d) => {
          setDashboard(d);
          loadReport(spec);
        })
        .catch((e) => setError(String(e)))
        .finally(() => setBusy(false));
    } else {
      streamOptimize(spec, {
        onProgress: setProgress,
        onResult: (r) => {
          if (r.best) {
            const winner: InputSpec = { assumptions: r.best.assumptions };
            analyze(winner)
              .then((d) => {
                setDashboard(d);
                loadReport(winner);
              })
              .catch((e) => setError(String(e)))
              .finally(() => setBusy(false));
          } else {
            setError("No feasible design satisfies those constraints.");
            setBusy(false);
          }
        },
        onError: (e) => {
          setError(String(e));
          setBusy(false);
        },
      });
    }
  }, [busy, config, mode, buildSpec, loadReport]);

  const reset = useCallback(() => {
    if (config) setValues(config.defaults);
    setSearch(INITIAL_SEARCH);
  }, [config]);

  const exportToml = useCallback(() => {
    let s = "[assumptions]\n";
    for (const [k, v] of Object.entries(values)) s += `${k} = ${v}\n`;
    if (mode === "optimize") {
      const ranges = Object.entries(search.ranges);
      if (ranges.length) {
        s += "\n[search.ranges]\n";
        for (const [k, [lo, hi]] of ranges) s += `${k} = [${lo}, ${hi}]\n`;
      }
      const cons = Object.entries(search.constraints).filter(([, v]) => v != null);
      if (cons.length) {
        s += "\n[search.constraints]\n";
        for (const [k, v] of cons) s += `${k} = ${v}\n`;
      }
      s += `\n[search]\nobjective = "${search.objective}"\n`;
    }
    const url = URL.createObjectURL(new Blob([s], { type: "text/plain" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "inputs.toml";
    a.click();
    URL.revokeObjectURL(url);
  }, [values, mode, search]);

  const downloadReport = useCallback(() => {
    if (!reportMd) return;
    const url = URL.createObjectURL(new Blob([reportMd], { type: "text/markdown" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "technical_report.md";
    a.click();
    URL.revokeObjectURL(url);
  }, [reportMd]);

  useShortcuts(
    useMemo(
      () => [
        { key: "enter", meta: true, run },
        { key: "o", run: () => setMode((m) => (m === "single" ? "optimize" : "single")) },
        { key: "r", run: reset },
        { key: "d", run: downloadReport },
        { key: "?", run: () => setShowKeys((s) => !s) },
        {
          key: "/",
          run: () => {
            const el = document.querySelector<HTMLInputElement>("#chat-anchor input");
            el?.focus();
          },
        },
      ],
      [run, reset, downloadReport],
    ),
  );

  const status = busy
    ? progress
      ? `${progress.message} · ${Math.round(progress.fraction * 100)}%`
      : mode === "optimize"
        ? "Searching designs…"
        : "Computing…"
    : dashboard
      ? "Ready"
      : "Idle — press Run";

  return (
    <div className="app">
      <StatusBar mode={mode} onMode={setMode} onRun={run} busy={busy} status={status} />
      <div className="workspace" style={{ "--rail-w": `${rail.width}px` } as React.CSSProperties}>
        <aside className="rail">
          <InputsPanel
            config={config}
            values={values}
            onChange={(k, v) => setValues((prev) => ({ ...prev, [k]: v }))}
            mode={mode}
            search={search}
            onSearch={setSearch}
            onExport={exportToml}
          />
        </aside>

        <Tooltip label="Drag to resize · double-click to reset" side="right">
          <div
            className={rail.dragging ? "rail-handle dragging" : "rail-handle"}
            onPointerDown={rail.onPointerDown}
            onDoubleClick={rail.reset}
            role="separator"
            aria-orientation="vertical"
            aria-label="Resize parameters panel"
          />
        </Tooltip>

        <main className="main">
          {error && (
            <div
              className="panel"
              style={{ padding: "var(--s3) var(--s4)", marginBottom: "var(--s4)", color: "var(--bad)" }}
            >
              <span className="label" style={{ color: "var(--bad)" }}>
                Error
              </span>
              <div className="mono" style={{ fontSize: 12 }}>
                {error}
              </div>
            </div>
          )}

          {busy && progress && (
            <div className="panel" style={{ padding: "var(--s4)", marginBottom: "var(--s4)" }}>
              <div className="label" style={{ marginBottom: 8 }}>
                {progress.message} — {progress.done}/{progress.total}
              </div>
              <div className="scanbar">
                <div className="fill" style={{ "--p": `${progress.fraction * 100}%` } as React.CSSProperties} />
                <div className="sheen" />
              </div>
            </div>
          )}

          {!dashboard && !busy && (
            <div className="panel rise" style={{ padding: "var(--s7)", textAlign: "center" }}>
              <div className="brand" style={{ fontSize: 18, marginBottom: 8 }}>
                GEOTHERM<span className="dot" style={{ color: "var(--cool)" }}>.</span>
              </div>
              <div style={{ color: "var(--text-dim)", maxWidth: 460, margin: "0 auto" }}>
                Set the parameters and press <span className="kbd">⌘↵</span> Run to evaluate the
                Utrecht geothermal heating + cooling system — resource, design, and least-cost LCoE.
              </div>
            </div>
          )}

          {dashboard && (
            <div className="grid">
              <div className="col-12 rise" style={{ animationDelay: "0ms" }}>
                <HeadlineStrip headline={dashboard.headline} doublets={dashboard.best.n_doublets} />
              </div>
              <div className="col-7 rise" style={{ animationDelay: "60ms" }}>
                <ResourceMap map={dashboard.resource_map} />
              </div>
              <div className="col-5 rise" style={{ animationDelay: "120ms" }}>
                <PercentilesChart data={dashboard.percentiles} />
              </div>
              <div className="col-6 rise" style={{ animationDelay: "180ms" }}>
                <DispatchChart design={dashboard.design} />
              </div>
              <div className="col-6 rise" style={{ animationDelay: "240ms" }}>
                <MonteCarloChart mc={dashboard.monte_carlo} />
              </div>
              <div className="col-7 rise" style={{ animationDelay: "300ms" }}>
                <TornadoChart rows={dashboard.tornado} />
              </div>
              <div className="col-5 rise" style={{ animationDelay: "360ms" }}>
                <ComparisonTable
                  candidates={dashboard.comparison}
                  bestDoublets={dashboard.best.n_doublets}
                />
              </div>
              <div className="col-7 rise" style={{ animationDelay: "420ms" }}>
                <ReportPanel
                  markdown={reportMd}
                  loading={reportLoading}
                  onLoad={() => loadReport(buildSpec())}
                />
              </div>
              <div id="chat-anchor" className="col-5 rise" style={{ animationDelay: "480ms" }}>
                <ChatDock context={reportMd ?? ""} />
              </div>
              <div className="col-12 rise" style={{ animationDelay: "540ms" }}>
                <DecisionLog spec={buildSpec()} />
              </div>
            </div>
          )}
        </main>
      </div>

      {showKeys && (
        <div
          onClick={() => setShowKeys(false)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.6)",
            display: "grid",
            placeItems: "center",
            zIndex: 50,
          }}
        >
          <div className="panel" style={{ padding: "var(--s5)", minWidth: 320 }}>
            <div className="label" style={{ marginBottom: "var(--s4)" }}>
              Keyboard shortcuts
            </div>
            {[
              ["⌘ / Ctrl + ↵", "Run"],
              ["O", "Toggle evaluate / optimise"],
              ["R", "Reset parameters"],
              ["D", "Download report"],
              ["/", "Focus chat"],
              ["?", "This overlay"],
            ].map(([k, d]) => (
              <div
                key={k}
                style={{ display: "flex", justifyContent: "space-between", gap: 24, padding: "5px 0" }}
              >
                <span className="kbd">{k}</span>
                <span style={{ color: "var(--text-dim)" }}>{d}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
