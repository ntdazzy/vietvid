"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { User, Mic, KeyRound, LogOut, Lock, Users, Loader2, BadgeCheck } from "lucide-react";
import { useMe } from "@/lib/query/hooks";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ChipGroup, Field, inputCls } from "@/components/ui/field";
import { clearSession } from "@/lib/auth/session";

const VOICE_KEY = "vietvid_default_voice";

export default function SettingsPage() {
  const me = useMe();
  const router = useRouter();
  const isLocal = me.data?.auth_mode === "dev";

  const [voice, setVoice] = useState<"female" | "male">("female");
  const [name, setName] = useState("");
  const [savingName, setSavingName] = useState(false);
  const [nameMsg, setNameMsg] = useState("");

  const [curPw, setCurPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [pwBusy, setPwBusy] = useState(false);
  const [pwMsg, setPwMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  useEffect(() => {
    const v = localStorage.getItem(VOICE_KEY);
    if (v === "male" || v === "female") setVoice(v);
  }, []);

  function pickVoice(v: "female" | "male") {
    setVoice(v);
    localStorage.setItem(VOICE_KEY, v);
  }

  async function saveName(e: React.FormEvent) {
    e.preventDefault();
    setSavingName(true);
    setNameMsg("");
    try {
      await api.updateProfile({ full_name: name.trim() });
      setNameMsg("Đã lưu.");
    } finally {
      setSavingName(false);
    }
  }

  async function changePw(e: React.FormEvent) {
    e.preventDefault();
    setPwBusy(true);
    setPwMsg(null);
    try {
      await api.changePassword(curPw, newPw);
      setPwMsg({ kind: "ok", text: "Đổi mật khẩu thành công. Các phiên khác đã đăng xuất." });
      setCurPw("");
      setNewPw("");
    } catch (err) {
      setPwMsg({ kind: "err", text: err instanceof Error ? err.message : "Đổi mật khẩu lỗi" });
    } finally {
      setPwBusy(false);
    }
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

      {/* hồ sơ */}
      <GlassCard className="p-5">
        <div className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-ink-low">
          <BadgeCheck className="h-4 w-4" /> Hồ sơ
        </div>
        <form onSubmit={saveName} className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <Field label="Tên hiển thị">
              <input
                className={inputCls}
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Tên của bạn"
              />
            </Field>
          </div>
          <Button type="submit" disabled={savingName}>
            {savingName ? <Loader2 className="h-4 w-4 animate-spin" /> : "Lưu"}
          </Button>
        </form>
        {nameMsg && <p className="mt-2 text-sm text-success">{nameMsg}</p>}
      </GlassCard>

      {/* đổi mật khẩu (chỉ local-auth) */}
      {isLocal && (
        <GlassCard className="p-5">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-ink-low">
            <Lock className="h-4 w-4" /> Đổi mật khẩu
          </div>
          <form onSubmit={changePw} className="flex flex-col gap-3">
            <Field label="Mật khẩu hiện tại">
              <input
                type="password"
                required
                className={inputCls}
                value={curPw}
                onChange={(e) => setCurPw(e.target.value)}
              />
            </Field>
            <Field label="Mật khẩu mới">
              <input
                type="password"
                required
                minLength={6}
                className={inputCls}
                value={newPw}
                onChange={(e) => setNewPw(e.target.value)}
                placeholder="Tối thiểu 6 ký tự"
              />
            </Field>
            {pwMsg && (
              <p className={`text-sm ${pwMsg.kind === "ok" ? "text-success" : "text-danger"}`}>
                {pwMsg.text}
              </p>
            )}
            <Button type="submit" disabled={pwBusy} className="self-start">
              {pwBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : "Đổi mật khẩu"}
            </Button>
          </form>
        </GlassCard>
      )}

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

      {/* thành viên */}
      <GlassCard className="p-5">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-ink-low">
          <Users className="h-4 w-4" /> Thành viên workspace
        </div>
        <p className="mb-3 text-sm text-ink-low">Mời cộng sự cùng tạo video trong workspace của bạn.</p>
        <Link href="/app/team">
          <Button variant="glass">Quản lý thành viên</Button>
        </Link>
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
