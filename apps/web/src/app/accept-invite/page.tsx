"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2, CheckCircle2, XCircle, Users } from "lucide-react";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api/endpoints";
import { isAuthed } from "@/lib/auth/session";

export default function AcceptInvitePage() {
  const router = useRouter();
  const [state, setState] = useState<"loading" | "ok" | "error" | "need-login">("loading");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get("token") || "";
    if (!token) {
      setState("error");
      setMsg("Thiếu mã lời mời.");
      return;
    }
    (async () => {
      if (!(await isAuthed())) {
        // nhớ token để chấp nhận sau khi đăng nhập
        sessionStorage.setItem("vietvid_pending_invite", token);
        setState("need-login");
        return;
      }
      try {
        const r = await api.acceptInvite(token);
        setMsg(r.detail || "Đã tham gia workspace.");
        setState("ok");
      } catch (err) {
        setMsg(err instanceof Error ? err.message : "Lời mời không hợp lệ hoặc đã hết hạn.");
        setState("error");
      }
    })();
  }, []);

  return (
    <AuthShell title="Lời mời tham gia">
      {state === "loading" && (
        <div className="flex items-center gap-3 text-ink-medium">
          <Loader2 className="h-5 w-5 animate-spin text-violet-300" /> Đang xử lý...
        </div>
      )}
      {state === "need-login" && (
        <>
          <div className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-4 text-sm text-ink-medium">
            <Users className="mt-0.5 h-5 w-5 shrink-0 text-violet-300" />
            <span>Đăng nhập (hoặc đăng ký bằng đúng email được mời) rồi mở lại liên kết để tham gia.</span>
          </div>
          <Link href="/login" className="mt-6 block">
            <Button size="lg" className="w-full">
              Đăng nhập / Đăng ký
            </Button>
          </Link>
        </>
      )}
      {state === "ok" && (
        <>
          <div className="flex items-center gap-3 rounded-xl border border-success/30 bg-success/[0.08] p-4 text-sm text-ink-medium">
            <CheckCircle2 className="h-5 w-5 shrink-0 text-success" /> {msg}
          </div>
          <Button size="lg" className="mt-6 w-full" onClick={() => router.push("/app/team")}>
            Xem thành viên
          </Button>
        </>
      )}
      {state === "error" && (
        <div className="flex items-start gap-3 rounded-xl border border-danger/30 bg-danger/[0.1] p-4 text-sm text-danger">
          <XCircle className="mt-0.5 h-5 w-5 shrink-0" /> {msg}
        </div>
      )}
    </AuthShell>
  );
}
