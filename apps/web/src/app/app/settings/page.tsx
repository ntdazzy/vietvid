"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { User, Mic, KeyRound, LogOut } from "lucide-react";
import { useMe } from "@/lib/query/hooks";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ChipGroup } from "@/components/ui/field";
import { clearSession } from "@/lib/auth/session";

const VOICE_KEY = "vietvid_default_voice";

export default function SettingsPage() {
  const me = useMe();
  const router = useRouter();
  const [voice, setVoice] = useState<"female" | "male">("female");

  useEffect(() => {
    const v = localStorage.getItem(VOICE_KEY);
    if (v === "male" || v === "female") setVoice(v);
  }, []);

  function pickVoice(v: "female" | "male") {
    setVoice(v);
    localStorage.setItem(VOICE_KEY, v);
  }

  return (
    <div className="flex max-w-2xl flex-col gap-6">
      <h1 className="text-2xl font-bold text-ink-high lg:text-[34px]">Cài đặt</h1>

      {/* tài khoản */}
      <GlassCard className="p-5">
        <div className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-ink-low">
          <User className="h-4 w-4" /> Tài khoản
        </div>
        {me.isLoading || !me.data ? (
          <Skeleton className="h-16 w-full" />
        ) : (
          <dl className="flex flex-col divide-y divide-white/[0.06] text-sm">
            <Row k="Email" v={me.data.email || "(dev)"} />
            <Row k="Workspace" v={<span className="font-mono text-xs">{me.data.org_id}</span>} />
            <Row k="Vai trò" v={<Badge tone="brand">{me.data.role}</Badge>} />
            <Row k="Chế độ auth" v={me.data.auth_mode} />
          </dl>
        )}
      </GlassCard>

      {/* giọng mặc định */}
      <GlassCard className="p-5">
        <div className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-ink-low">
          <Mic className="h-4 w-4" /> Giọng mặc định
        </div>
        <ChipGroup
          value={voice}
          onChange={(v) => pickVoice(v as "female" | "male")}
          options={[
            { value: "female", label: "Nữ" },
            { value: "male", label: "Nam" },
          ]}
        />
        <p className="mt-3 text-xs text-ink-low">Áp dụng làm gợi ý mặc định khi tạo video.</p>
      </GlassCard>

      {/* API keys (Product C) */}
      <GlassCard className="p-5">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-ink-low">
          <KeyRound className="h-4 w-4" /> API keys (cho nhà phát triển)
        </div>
        <p className="text-sm text-ink-low">
          Gọi engine VietVid qua API / white-label. <Badge tone="neutral">Sắp có (M5)</Badge>
        </p>
      </GlassCard>

      <Button
        variant="glass"
        className="gap-2 self-start"
        onClick={() => {
          clearSession();
          router.push("/");
        }}
      >
        <LogOut className="h-4 w-4" /> Đăng xuất
      </Button>
    </div>
  );
}

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 py-2.5">
      <dt className="text-ink-low">{k}</dt>
      <dd className="text-right text-ink-high">{v}</dd>
    </div>
  );
}
