"use client";

import { useEffect, useState } from "react";
import { getToken } from "@/lib/auth/session";

/** Tải tài nguyên cần Bearer (vd video job) → objectURL để <video>/<a download> dùng. */
export function useAuthedBlob(url: string | null) {
  const [blobUrl, setBlobUrl] = useState<string>();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!url) return;
    let obj: string | undefined;
    let alive = true;
    setLoading(true);
    (async () => {
      const token = await getToken();
      const res = await fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
      if (res.ok && alive) {
        obj = URL.createObjectURL(await res.blob());
        setBlobUrl(obj);
      }
      if (alive) setLoading(false);
    })();
    return () => {
      alive = false;
      if (obj) URL.revokeObjectURL(obj);
    };
  }, [url]);

  return { blobUrl, loading };
}
