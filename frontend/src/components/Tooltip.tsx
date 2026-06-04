import { Children, cloneElement, useCallback, useId, useRef, useState } from "react";
import type { FocusEvent, MouseEvent, ReactElement, ReactNode } from "react";
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

type Point = { x: number; y: number };

function anchorPoint(rect: DOMRect, side: TooltipSide): Point {
  switch (side) {
    case "bottom":
      return { x: rect.left + rect.width / 2, y: rect.bottom };
    case "left":
      return { x: rect.left, y: rect.top + rect.height / 2 };
    case "right":
      return { x: rect.right, y: rect.top + rect.height / 2 };
    default:
      return { x: rect.left + rect.width / 2, y: rect.top };
  }
}

/** A styled, portalled tooltip that replaces the native `title` attribute.
    Attaches directly to its child via cloneElement — no extra DOM, so it is safe
    inside grid/flex layouts. Opens on hover and on keyboard focus. */
export function Tooltip({ label, side = "top", children }: TooltipProps): ReactNode {
  const [pos, setPos] = useState<Point | null>(null);
  const timer = useRef<number | undefined>(undefined);
  const id = useId();

  const open = useCallback(
    (el: HTMLElement) => {
      window.clearTimeout(timer.current);
      timer.current = window.setTimeout(() => {
        setPos(anchorPoint(el.getBoundingClientRect(), side));
      }, DELAY_MS);
    },
    [side],
  );

  const close = useCallback(() => {
    window.clearTimeout(timer.current);
    setPos(null);
  }, []);

  const child = Children.only(children);
  const prev = child.props as ExistingHandlers;

  // We only attach hover/focus handlers to the trigger; no ref is passed or read
  // (the tooltip position comes from the event's currentTarget). The rule can't
  // see that, so it false-positives on cloneElement here.
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
    "aria-describedby": pos ? id : undefined,
  });

  return (
    <>
      {trigger}
      {pos !== null &&
        createPortal(
          <span
            role="tooltip"
            id={id}
            className={`tooltip tooltip-${side}`}
            style={{ left: pos.x, top: pos.y }}
          >
            {label}
          </span>,
          document.body,
        )}
    </>
  );
}
