import { useMemo } from "react";

const KEY = "fpl-comanager-user-id";

function randomId(): string {
  return `user-${crypto.randomUUID?.() ?? String(Date.now())}`;
}

export function useStableUserId(): string {
  return useMemo(() => {
    try {
      let id = localStorage.getItem(KEY);
      if (!id) {
        id = randomId();
        localStorage.setItem(KEY, id);
      }
      return id;
    } catch {
      return randomId();
    }
  }, []);
}
