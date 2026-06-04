import { useState } from "react";
import type { CSSProperties } from "react";

import { streamWorkflow } from "../api/client";
import type { InputSpec, ProgressEvent, WorkflowPayload, WorkflowStep } from "../api/types";
import { Panel } from "./Panel";

interface DecisionLogProps {
  spec: InputSpec;
}

/** Format a metric value compactly: integers stay whole, fractions get 2 dp. */
function fmtMetric(v: number): string {
  if (!Number.isFinite(v)) return "—";
  if (Number.isInteger(v)) return String(v);
  const abs = Math.abs(v);
  if (abs >= 100) return v.toFixed(0);
  if (abs >= 1) return v.toFixed(2);
  return v.toFixed(3);
}

/** Agentic workflow decision log with live streaming progress. */
export function DecisionLog({ spec }: DecisionLogProps) {
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [summary, setSummary] = useState<{ lcoe: number; doublets: number } | null>(null);
  const [progress, setProgress] = useState<ProgressEvent | null>(null);
  const [busy, setBusy] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const run = (): void => {
    setSteps([]);
    setSummary(null);
    setProgress(null);
    setError(null);
    setBusy(true);
    streamWorkflow(spec, {
      onProgress: (p: ProgressEvent) => setProgress(p),
      onResult: (r: WorkflowPayload) => {
        setSteps(r.steps);
        setSummary({ lcoe: r.lcoe_eur_per_gj, doublets: r.n_doublets });
        setBusy(false);
      },
      onError: () => {
        setError("Workflow stream failed.");
        setBusy(false);
      },
    });
  };

  const pct = progress ? `${(progress.fraction * 100).toFixed(0)}%` : "0%";

  return (
    <Panel
      label="AGENTIC WORKFLOW"
      accent="heat"
      right={
        <button className="btn" onClick={run} disabled={busy}>
          RUN AGENT
        </button>
      }
    >
      {busy && (
        <div style={{ marginBottom: "var(--s4, 16px)" }}>
          <div
            style={{
              display: "flex",
              alignItems: "baseline",
              justifyContent: "space-between",
              marginBottom: 8,
              gap: 12,
            }}
          >
            <span className="mono" style={{ fontSize: 11, color: "var(--text-dim)" }}>
              {progress?.message ?? "Initializing agent…"}
            </span>
            <span className="mono num" style={{ fontSize: 11, color: "var(--cool-hi)" }}>
              {pct}
            </span>
          </div>
          <div className="scanbar" style={{ "--p": pct } as CSSProperties}>
            <span className="fill" />
            <span className="sheen" />
          </div>
        </div>
      )}

      {error && (
        <div
          className="mono"
          style={{ fontSize: 11, color: "var(--bad)", marginBottom: "var(--s3, 12px)" }}
        >
          {error}
        </div>
      )}

      {summary && (
        <div
          style={{
            display: "flex",
            gap: 24,
            paddingBottom: "var(--s3, 12px)",
            marginBottom: "var(--s3, 12px)",
            borderBottom: "1px solid var(--line)",
          }}
        >
          <div className="metric">
            <span className="metric-value" style={{ fontSize: 20, color: "var(--cool-hi)" }}>
              {summary.lcoe.toFixed(2)}
              <span className="metric-unit"> €/GJ</span>
            </span>
            <span className="label" style={{ color: "var(--text-faint)" }}>
              LCOE
            </span>
          </div>
          <div className="metric">
            <span className="metric-value" style={{ fontSize: 20, color: "var(--text)" }}>
              {summary.doublets}
              <span className="metric-unit"> doublets</span>
            </span>
            <span className="label" style={{ color: "var(--text-faint)" }}>
              SELECTED
            </span>
          </div>
        </div>
      )}

      {steps.length > 0 ? (
        <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "var(--s3, 12px)" }}>
          {steps.map((step, i) => {
            const metrics = Object.entries(step.metrics);
            return (
              <li
                key={`${step.name}-${i}`}
                style={{
                  display: "flex",
                  gap: 14,
                  alignItems: "flex-start",
                  borderLeft: "1px solid var(--line)",
                  paddingLeft: 14,
                  marginLeft: 12,
                }}
              >
                <span
                  className="mono num"
                  style={{
                    flex: "0 0 auto",
                    width: 26,
                    height: 26,
                    marginLeft: -27,
                    display: "grid",
                    placeItems: "center",
                    borderRadius: "50%",
                    border: "1px solid var(--line-strong)",
                    background: "var(--bg-0)",
                    color: "var(--cool-hi)",
                    fontSize: 12,
                  }}
                >
                  {i + 1}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    className="mono"
                    style={{
                      color: "var(--cool-hi)",
                      fontSize: 13,
                      letterSpacing: "0.02em",
                      marginBottom: 3,
                    }}
                  >
                    {step.name}
                  </div>
                  <div
                    style={{
                      fontFamily: "var(--font-sans)",
                      fontSize: 12,
                      color: "var(--text-dim)",
                      marginBottom: 4,
                    }}
                  >
                    {step.action}
                  </div>
                  <div
                    style={{
                      fontFamily: "var(--font-sans)",
                      fontSize: 13,
                      color: "var(--text)",
                      lineHeight: 1.5,
                    }}
                  >
                    {step.decision}
                  </div>
                  {metrics.length > 0 && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
                      {metrics.map(([k, v]) => (
                        <span key={k} className="tag">
                          {k}
                          <span style={{ color: "var(--text)", marginLeft: 6 }}>{fmtMetric(v)}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      ) : (
        !busy && (
          <div
            style={{
              padding: "40px 24px",
              textAlign: "center",
            }}
          >
            <span className="label" style={{ color: "var(--text-faint)" }}>
              Run the agent to generate a decision log.
            </span>
          </div>
        )
      )}
    </Panel>
  );
}
