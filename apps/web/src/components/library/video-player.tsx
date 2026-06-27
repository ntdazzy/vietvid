"use client";

import { useEffect, useState } from "react";
import { Loader2, Download, Share2, Check } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { Button } from "@/components/ui/button";

export function VideoPlayer({ jobId }: { jobId: string }) {
  const [url, setUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let alive = true;
    api
      .getVideoSignedUrl(jobId)
      .then((u) => alive && setUrl(u))
      .catch(() => alive && setUrl(null))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [jobId]);

  async function share() {
    try {
      const { share_url } = await api.getShareUrl(jobId);
      await navigator.clipboard.writeText(share_url);
    } catch {
      if (url) await navigator.clipboard.writeText(url);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="overflow-hidden rounded-xl border border-white/10 bg-black">
        {url ? (
          <video src={url} controls autoPlay loop className="max-h-[64vh] w-auto" />
        ) : (
          <div className="grid h-72 w-44 place-items-center text-ink-low">
            {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : "Không tải được video"}
          </div>
        )}
      </div>
      {url && (
        <div className="flex gap-2">
          <a href={url} download={`vietvid-${jobId}.mp4`}>
            <Button className="gap-2">
              <Download className="h-4 w-4" /> Tải MP4
            </Button>
          </a>
          <Button variant="glass" className="gap-2" onClick={share}>
            {copied ? <Check className="h-4 w-4 text-success" /> : <Share2 className="h-4 w-4" />}
            {copied ? "Đã chép link" : "Chia sẻ"}
          </Button>
        </div>
      )}
    </div>
  );
}
