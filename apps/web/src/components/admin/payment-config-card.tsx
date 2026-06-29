"use client";

import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Landmark, KeyRound, Loader2, ShieldCheck, AlertTriangle, Check, Wallet } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Field, inputCls } from "@/components/ui/field";
import { cn } from "@/lib/utils/cn";
import type { PaymentConfig } from "@/lib/api/types";

const METHODS: { key: keyof PaymentConfig["enabled"]; label: string }[] = [
  { key: "bank_qr", label: "Chuyển khoản QR" },
  { key: "momo", label: "MoMo" },
  { key: "vnpay", label: "VNPay" },
];

/** Admin: cấu hình phương thức thanh toán (bank + key). Secret hiển thị '••••', chỉ ghi khi đổi. */
export function PaymentConfigCard() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["admin-payment-config"], queryFn: api.adminPaymentConfig });
  const [form, setForm] = useState<PaymentConfig | null>(null);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  useEffect(() => {
    if (q.data && !form) setForm(q.data);
  }, [q.data, form]);

  if (q.isLoading || !form) {
    return (
      <GlassCard className="grid place-items-center p-10">
        <Loader2 className="h-5 w-5 animate-spin text-ink-low" />
      </GlassCard>
    );
  }

  const envOnly = form.secrets_storage === "env-only";
  const set = (k: keyof PaymentConfig, v: string) => setForm((f) => (f ? { ...f, [k]: v } : f));
  const toggle = (k: keyof PaymentConfig["enabled"]) =>
    setForm((f) => (f ? { ...f, enabled: { ...f.enabled, [k]: !f.enabled[k] } } : f));

  async function save() {
    if (!form) return;
    setSaving(true);
    setMsg(null);
    try {
      const out = await api.adminSetPaymentConfig(form);
      setForm(out);
      qc.setQueryData(["admin-payment-config"], out);
      setMsg({ kind: "ok", text: "Đã lưu cấu hình thanh toán." });
    } catch (e) {
      setMsg({ kind: "err", text: e instanceof Error ? e.message : "Lưu lỗi" });
    } finally {
      setSaving(false);
    }
  }

  return (
    <GlassCard className="flex flex-col gap-5 p-5">
      <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-ink-low">
        <Wallet className="h-4 w-4 text-emerald-300" /> Phương thức thanh toán
      </div>

      {envOnly && (
        <div className="flex items-start gap-2 rounded-xl border border-hold/30 bg-hold/[0.08] px-3.5 py-2.5 text-xs text-hold">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>
            Chưa đặt <span className="font-mono">VIETVID_CONFIG_SECRET</span> → không lưu được KEY/SECRET qua giao diện
            (chỉ đọc từ env). Đặt biến này (chuỗi bất kỳ, giữ bí mật) rồi khởi động lại backend để lưu key an toàn (mã hoá).
          </span>
        </div>
      )}

      {/* bật/tắt phương thức */}
      <div className="flex flex-wrap gap-2">
        {METHODS.map((m) => {
          const on = form.enabled[m.key];
          return (
            <button
              key={m.key}
              type="button"
              onClick={() => toggle(m.key)}
              className={cn(
                "rounded-lg border px-3.5 py-1.5 text-sm transition-colors",
                on
                  ? "border-emerald-500/60 bg-emerald-500/15 text-ink-high"
                  : "border-white/10 text-ink-low hover:border-white/25",
              )}
            >
              {on ? "● " : "○ "}
              {m.label}
            </button>
          );
        })}
      </div>

      {/* ngân hàng nhận (bank-QR) */}
      <div>
        <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-ink-low">
          <Landmark className="h-3.5 w-3.5 text-violet-300" /> Ngân hàng nhận (QR)
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Mã BIN (vd MB 970422)">
            <input className={inputCls} value={form.bank_bin} onChange={(e) => set("bank_bin", e.target.value)} placeholder="970422" />
          </Field>
          <Field label="Số tài khoản">
            <input className={inputCls} value={form.bank_account} onChange={(e) => set("bank_account", e.target.value)} />
          </Field>
          <Field label="Tên chủ tài khoản (IN HOA)">
            <input className={inputCls} value={form.bank_account_name} onChange={(e) => set("bank_account_name", e.target.value)} />
          </Field>
          <Field label="Tên ngân hàng">
            <input className={inputCls} value={form.bank_name} onChange={(e) => set("bank_name", e.target.value)} placeholder="MBBank" />
          </Field>
        </div>
      </div>

      {/* secret: webhook token + momo/vnpay key */}
      <div>
        <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-ink-low">
          <KeyRound className="h-3.5 w-3.5 text-rose-300" /> Khoá / token (mã hoá khi lưu) — để '••••' = không đổi
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Webhook token (SePay / poller)">
            <input className={inputCls} value={form.webhook_token} onChange={(e) => set("webhook_token", e.target.value)} autoComplete="off" />
          </Field>
          <div />
          <Field label="MoMo partnerCode">
            <input className={inputCls} value={form.momo_partner} onChange={(e) => set("momo_partner", e.target.value)} autoComplete="off" />
          </Field>
          <Field label="MoMo accessKey">
            <input className={inputCls} value={form.momo_access} onChange={(e) => set("momo_access", e.target.value)} autoComplete="off" />
          </Field>
          <Field label="MoMo secretKey">
            <input className={inputCls} value={form.momo_secret} onChange={(e) => set("momo_secret", e.target.value)} autoComplete="off" />
          </Field>
          <div />
          <Field label="VNPay TmnCode">
            <input className={inputCls} value={form.vnpay_tmn} onChange={(e) => set("vnpay_tmn", e.target.value)} autoComplete="off" />
          </Field>
          <Field label="VNPay HashSecret">
            <input className={inputCls} value={form.vnpay_hash} onChange={(e) => set("vnpay_hash", e.target.value)} autoComplete="off" />
          </Field>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Button onClick={save} disabled={saving} className="gap-2">
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />} Lưu cấu hình
        </Button>
        {msg && (
          <span className={cn("flex items-center gap-1.5 text-sm", msg.kind === "ok" ? "text-success" : "text-danger")}>
            {msg.kind === "ok" ? <ShieldCheck className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
            {msg.text}
          </span>
        )}
      </div>
    </GlassCard>
  );
}
