import { Children, cloneElement, useCallback, useId, useLayoutEffect, useRef, useState } from "react";
import type { CSSProperties, FocusEvent, MouseEvent, ReactElement, ReactNode } from "react";
import { createPortal } from "react-dom";

export type TooltipSide = "top" | "bottom" | "left" | "right";

interface TooltipProps {
  label: ReactNode;
  side?: TooltipSide;
  /** A single hoverable/focusable element (button, span, div…). No wrapper is added. */
  children: ReactElement;
}

/** Handlers the trigger may already carry — chained, not clobbered. */
type ExistingHandlers = Partial<{
  onMouseEnter: (e: MouseEvent<HTMLElement>) => void;
  onMouseLeave: (e: MouseEvent<HTMLElement>) => void;
  onFocus: (e: FocusEvent<HTMLElement>) => void;
  onBlur: (e: FocusEvent<HTMLElement>) => void;
}>;

const DELAY_MS = 200;
const MARGIN = 8;

/** A styled, portalled tooltip that replaces the native `title` attribute. Attaches
    directly to its child via cloneElement (no wrapper DOM, safe in grid/flex), opens
    on hover and keyboard focus, and is measured + clamped to stay inside the viewport. */
export function Tooltip({ label, side = "top", children }: TooltipProps): ReactNode {
  const [anchor, setAnchor] = useState<DOMRect | null>(null);
  const [coords, setCoords] = useState<{ left: number; top: number } | null>(null);
  const tip = useRef<HTMLSpanElement | null>(null);
  const timer = useRef<number | undefined>(undefined);
  const id = useId();

  const open = useCallback((el: HTMLElement) => {
    window.clearTimeout(timer.current);
    const rect = el.getBoundingClientRect();
    timer.current = window.setTimeout(() => {
      setAnchor(rect);
      setCoords(null);
    }, DELAY_MS);
  }, []);

  const close = useCallback(() => {
    window.clearTimeout(timer.current);
    setAnchor(null);
    setCoords(null);
  }, []);

  // Measure the rendered tooltip, place it on the requested side, then clamp to the viewport.
  useLayoutEffect(() => {
    const el = tip.current;
    if (!anchor || !el) return;
    const t = el.getBoundingClientRect();
    const cx = anchor.left + anchor.width / 2;
    const cy = anchor.top + anchor.height / 2;
    let left: number;
    let top: number;
    if (side === "bottom") {
      left = cx - t.width / 2;
      top = anchor.bottom + MARGIN;
    } else if (side === "left") {
      left = anchor.left - t.width - MARGIN;
      top = cy - t.height / 2;
    } else if (side === "right") {
      left = anchor.right + MARGIN;
      top = cy - t.height / 2;
    } else {
      left = cx - t.width / 2;
      top = anchor.top - t.height - MARGIN;
    }
    left = Math.min(Math.max(left, MARGIN), window.innerWidth - t.width - MARGIN);
    top = Math.min(Math.max(top, MARGIN), window.innerHeight - t.height - MARGIN);
    setCoords({ left, top });
  }, [anchor, side]);

  const child = Children.only(children);
  const prev = child.props as ExistingHandlers;

  // We only attach hover/focus handlers; no ref is passed or read (position comes from
  // the event's currentTarget). The rule can't see that, so it false-positives here.
  // eslint-disable-next-line react-hooks/refs
  const trigger = cloneElement(child as ReactElement<Record<string, unknown>>, {
    onMouseEnter: (e: MouseEvent<HTMLElement>) => {
      prev.onMouseEnter?.(e);
      open(e.currentTarget);
    },
    onMouseLeave: (e: MouseEvent<HTMLElement>) => {
      prev.onMouseLeave?.(e);
      close();
    },
    onFocus: (e: FocusEvent<HTMLElement>) => {
      prev.onFocus?.(e);
      open(e.currentTarget);
    },
    onBlur: (e: FocusEvent<HTMLElement>) => {
      prev.onBlur?.(e);
      close();
    },
    "aria-describedby": anchor ? id : undefined,
  });

  const style: CSSProperties = coords
    ? { left: coords.left, top: coords.top, opacity: 1 }
    : { left: anchor?.left ?? 0, top: anchor?.top ?? 0, opacity: 0 };

  return (
    <>
      {trigger}
      {anchor !== null &&
        createPortal(
          <span ref={tip} role="tooltip" id={id} className={`tooltip tooltip-${side}`} style={style}>
            {label}
          </span>,
          document.body,
        )}
    </>
  );
}
