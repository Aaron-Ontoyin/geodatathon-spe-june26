import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Panel } from "./Panel";

interface ReportPanelProps {
  markdown: string | null;
  loading: boolean;
  onLoad: () => void;
}

/** Renders the generated transparency report as markdown, with download. */
export function ReportPanel({ markdown, loading, onLoad }: ReportPanelProps) {
  const download = (): void => {
    if (!markdown) return;
    const blob = new Blob([markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "technical_report.md";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Panel
      label="TRANSPARENCY REPORT"
      right={
        <button className="btn" onClick={download} disabled={!markdown}>
          DOWNLOAD .md
        </button>
      }
    >
      {markdown ? (
        <div className="prose" style={{ maxHeight: 520, overflow: "auto" }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
        </div>
      ) : loading ? (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 16,
            padding: "48px 24px",
          }}
        >
          <span className="label" style={{ color: "var(--text-dim)" }}>
            Generating&hellip;
          </span>
          <div className="scanbar" style={{ width: 220 }}>
            <span className="sheen" />
          </div>
        </div>
      ) : (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 18,
            padding: "48px 24px",
          }}
        >
          <span className="label" style={{ color: "var(--text-faint)" }}>
            No report generated yet
          </span>
          <button className="btn" onClick={onLoad}>
            GENERATE REPORT
          </button>
        </div>
      )}
    </Panel>
  );
}
