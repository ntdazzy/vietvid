import Link from "next/link";
import { Compass } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="mesh-bg grid min-h-dvh place-items-center px-4 text-center">
      <div className="max-w-md">
        <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-grad-brand-soft text-violet-300">
          <Compass className="h-7 w-7" />
        </div>
        <div className="mt-6 font-numeric text-6xl font-bold text-gradient">404</div>
        <h1 className="mt-2 text-2xl font-bold text-ink-high">Không tìm thấy trang</h1>
        <p className="mt-2 text-ink-low">
          Trang bạn tìm không tồn tại hoặc đã được chuyển đi.
        </p>
        <div className="mt-6 flex items-center justify-center gap-3">
          <Link href="/">
            <Button>Về trang chủ</Button>
          </Link>
          <Link href="/app">
            <Button variant="glass">Vào ứng dụng</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
