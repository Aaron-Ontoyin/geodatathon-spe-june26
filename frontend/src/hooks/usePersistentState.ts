import { useEffect, useState } from "react";
import type { Dispatch, SetStateAction } from "react";

/** Drop-in `useState` that persists the value to localStorage under `key`.
    Falls back to `initial` if nothing is stored or the stored value is corrupt. */
export function usePersistentState<T>(
  key: string,
  initial: T,
): [T, Dispatch<SetStateAction<T>>] {
  const [value, setValue] = useState<T>(() => {
    const raw = window.localStorage.getItem(key);
    if (raw === null) return initial;
    try {
      return JSON.parse(raw) as T;
    } catch {
      return initial;
    }
  });

  useEffect(() => {
    window.localStorage.setItem(key, JSON.stringify(value));
  }, [key, value]);

  return [value, setValue];
}
