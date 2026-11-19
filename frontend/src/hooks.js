import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
export function useResource(path, interval = 0) {
  const [data, setData] = useState(null),
    [error, setError] = useState("");
  const pathRef = useRef(path);
  pathRef.current = path;
  const revision = useRef(0);
  const refresh = useCallback(async () => {
    const rev = ++revision.current;
    try {
      const value = await api.request(path);
      if (pathRef.current === path && rev === revision.current) {
        setData(value);
        setError("");
      }
    } catch (e) {
      if (pathRef.current === path && rev === revision.current)
        setError(e.message);
    }
  }, [path]);
  useEffect(() => {
    setData(null);
    void refresh();
    if (interval) {
      const id = window.setInterval(() => {
        if (!document.hidden) void refresh();
      }, interval);
      return () => window.clearInterval(id);
    }
  }, [refresh, interval]);
  return {
    data,
    error,
    refresh,
    setData,
  };
}
export function useClock() {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}
export function usePreference(key, initial) {
  const [value, setValue] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(key) || "null") ?? initial;
    } catch {
      return initial;
    }
  });
  useEffect(
    () => localStorage.setItem(key, JSON.stringify(value)),
    [key, value],
  );
  return [value, setValue];
}
