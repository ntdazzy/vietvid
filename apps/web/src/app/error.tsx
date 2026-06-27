"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error(error);
  }, [error]);

  return (
    <div className="mesh-bg grid min-h-dvh place-items-center px-4 text-center">
      <div className="max-w-md">
        <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-danger/[0.12] text-danger">
          <AlertTriangle className="h-7 w-7" />
        </div>
        <h1 className="mt-6 text-2xl font-bold text-ink-high">Có lỗi xảy ra</h1>
        <p className="mt-2 text-ink-low">
          Hệ thống gặp sự cố khi tải trang này. Bạn thử lại nhé — nếu vẫn lỗi, hãy quay về trang chủ.
        </p>
        <div className="mt-6 flex items-center justify-center gap-3">
          <Button onClick={reset} className="gap-2">
            <RotateCcw className="h-4 w-4" /> Thử lại
          </Button>
          <Link href="/">
            <Button variant="glass">Về trang chủ</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
