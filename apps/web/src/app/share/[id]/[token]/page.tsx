"use client";

import { use } from "react";
import Link from "next/link";
import { Download, Sparkles } from "lucide-react";
import { API_BASE_URL } from "@/lib/config";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";

export default function SharePage({
  params,
}: {
  params: Promise<{ id: string; token: string }>;
}) {
  const { id, token } = use(params);
  const videoUrl = `${API_BASE_URL}/v1/media/video/${id}?token=${encodeURIComponent(token)}`;

  return (
    <div className="mesh-bg flex min-h-dvh flex-col">
      <header className="mx-auto flex w-full max-w-5xl items-center justify-between px-4 py-5">
        <Link href="/">
          <Logo />
        </Link>
        <Link href="/login">
          <Button size="sm">Tạo video của bạn</Button>
        </Link>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center gap-6 px-4 pb-16">
        <div className="w-full overflow-hidden rounded-2xl border border-white/10 bg-black shadow-[0_24px_70px_-20px_rgba(0,0,0,0.8)]">
          {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
          <video src={videoUrl} controls autoPlay loop playsInline className="mx-auto max-h-[72vh] w-auto" />
        </div>

        <div className="flex items-center gap-3">
          <a href={videoUrl} download={`vietvid-${id}.mp4`}>
            <Button className="gap-2">
              <Download className="h-4 w-4" /> Tải MP4
            </Button>
          </a>
          <Link href="/login">
            <Button variant="glass" className="gap-2">
              <Sparkles className="h-4 w-4" /> Tạo video AI giọng Việt
            </Button>
          </Link>
        </div>

        <p className="text-center text-sm text-ink-low">
          Video được tạo bằng <span className="text-gradient font-semibold">VietVid</span> — AI tạo video bán hàng giọng Việt thật.
        </p>
      </main>
    </div>
  );
}
