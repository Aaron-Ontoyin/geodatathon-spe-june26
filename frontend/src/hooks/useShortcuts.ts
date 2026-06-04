import { useEffect } from "react";

export interface Shortcut {
  /** Single key (lower-case), e.g. "o", "r", "/", "?". */
  key: string;
  /** Require Cmd/Ctrl to be held. */
  meta?: boolean;
  run: () => void;
}

/** Register global keyboard shortcuts (ignored while typing in inputs unless meta). */
export function useShortcuts(shortcuts: Shortcut[]): void {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      const typing =
        target?.tagName === "INPUT" || target?.tagName === "TEXTAREA" || target?.isContentEditable;
      for (const s of shortcuts) {
        const metaOk = s.meta ? e.metaKey || e.ctrlKey : !e.metaKey && !e.ctrlKey;
        if (e.key.toLowerCase() === s.key && metaOk) {
          if (typing && !s.meta) continue; // don't hijack plain keys while typing
          e.preventDefault();
          s.run();
          return;
        }
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [shortcuts]);
}
