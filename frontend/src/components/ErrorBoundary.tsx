import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/** Catches render-time crashes so the app shows the cause instead of a blank page. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("App crashed:", error, info.componentStack);
  }

  render(): ReactNode {
    const { error } = this.state;
    if (!error) return this.props.children;
    return (
      <div style={{ padding: "2rem", fontFamily: "monospace", color: "#8c4626", maxWidth: 900 }}>
        <h2 style={{ marginTop: 0 }}>The app hit an error and could not render.</h2>
        <p>Try clearing saved state, then reload:</p>
        <pre style={{ background: "#f4f6ee", padding: "0.75rem", borderRadius: 6 }}>
          localStorage.clear(); location.reload()
        </pre>
        <p>Error:</p>
        <pre style={{ background: "#f4f6ee", padding: "0.75rem", borderRadius: 6, whiteSpace: "pre-wrap" }}>
          {error.message}
          {"\n\n"}
          {error.stack}
        </pre>
      </div>
    );
  }
}
