import { useCallback, useEffect, useRef, useState } from "react";

interface ResizableOptions {
  /** localStorage key the width is persisted under. */
  storageKey: string;
  initial: number;
  min: number;
  max: number;
}

interface Resizable {
  width: number;
  dragging: boolean;
  onPointerDown: (e: React.PointerEvent) => void;
  reset: () => void;
}

const clamp = (n: number, lo: number, hi: number): number => Math.min(Math.max(n, lo), hi);

/** A persisted, pointer-draggable width — e.g. for a resizable sidebar.
    Window listeners attach only while dragging; double-click `reset` restores `initial`. */
export function useResizable({ storageKey, initial, min, max }: ResizableOptions): Resizable {
  const [width, setWidth] = useState<number>(() => {
    const saved = Number(window.localStorage.getItem(storageKey));
    return Number.isFinite(saved) && saved > 0 ? clamp(saved, min, max) : initial;
  });
  const [dragging, setDragging] = useState(false);
  const origin = useRef<{ x: number; w: number } | null>(null);

  const onPointerMove = useCallback(
    (e: PointerEvent) => {
      if (!origin.current) return;
      setWidth(clamp(origin.current.w + (e.clientX - origin.current.x), min, max));
    },
    [min, max],
  );

  const onPointerUp = useCallback(() => {
    origin.current = null;
    setDragging(false);
    document.body.style.userSelect = "";
    document.body.style.cursor = "";
  }, []);

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      e.preventDefault();
      origin.current = { x: e.clientX, w: width };
      setDragging(true);
      document.body.style.userSelect = "none";
      document.body.style.cursor = "col-resize";
    },
    [width],
  );

  useEffect(() => {
    if (!dragging) return;
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    return () => {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
    };
  }, [dragging, onPointerMove, onPointerUp]);

  useEffect(() => {
    window.localStorage.setItem(storageKey, String(Math.round(width)));
  }, [storageKey, width]);

  const reset = useCallback(() => setWidth(initial), [initial]);

  return { width, dragging, onPointerDown, reset };
}
