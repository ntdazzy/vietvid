"use client";

import { Loader2, Download } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { useAuthedBlob } from "@/lib/query/use-authed-blob";
import { Button } from "@/components/ui/button";

export function VideoPlayer({ jobId }: { jobId: string }) {
  const { blobUrl, loading } = useAuthedBlob(api.videoUrl(jobId));

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="overflow-hidden rounded-xl border border-white/10 bg-black">
        {blobUrl ? (
          <video src={blobUrl} controls autoPlay loop className="max-h-[64vh] w-auto" />
        ) : (
          <div className="grid h-72 w-44 place-items-center text-ink-low">
            {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : "Không tải được video"}
          </div>
        )}
      </div>
      {blobUrl && (
        <a href={blobUrl} download={`vietvid-${jobId}.mp4`}>
          <Button className="gap-2">
            <Download className="h-4 w-4" /> Tải MP4 (không watermark)
          </Button>
        </a>
      )}
    </div>
  );
}
