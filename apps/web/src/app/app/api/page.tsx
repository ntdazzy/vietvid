"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { KeyRound, Webhook, Copy, Check, Trash2, Loader2, Plus, Terminal } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { API_BASE_URL } from "@/lib/config";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { inputCls } from "@/components/ui/field";
import { cn } from "@/lib/utils/cn";

export default function ApiPage() {
  const qc = useQueryClient();
  const keys = useQuery({ queryKey: ["api-keys"], queryFn: api.apiKeys });
  const hooks = useQuery({ queryKey: ["webhooks"], queryFn: api.webhooks });

  const [keyName, setKeyName] = useState("");
  const [newKey, setNewKey] = useState<string | null>(null);
  const [hookUrl, setHookUrl] = useState("");
  const [newSecret, setNewSecret] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  function copy(text: string, tag: string) {
    navigator.clipboard.writeText(text);
    setCopied(tag);
    setTimeout(() => setCopied(null), 1500);
  }

  async function createKey() {
    setBusy(true);
    try {
      const r = await api.createApiKey(keyName.trim() || "Khoá mới");
      setNewKey(r.key);
      setKeyName("");
      qc.invalidateQueries({ queryKey: ["api-keys"] });
    } finally {
      setBusy(false);
    }
  }
  async function revokeKey(id: string) {
    await api.revokeApiKey(id);
    qc.invalidateQueries({ queryKey: ["api-keys"] });
  }
  async function createHook() {
    if (!hookUrl.trim().startsWith("http")) return;
    setBusy(true);
    try {
      const r = await api.createWebhook(hookUrl.trim());
      setNewSecret(r.secret);
      setHookUrl("");
      qc.invalidateQueries({ queryKey: ["webhooks"] });
    } finally {
      setBusy(false);
    }
  }
  async function deleteHook(id: string) {
    await api.deleteWebhook(id);
    qc.invalidateQueries({ queryKey: ["webhooks"] });
  }

  const curl = `curl -X POST ${API_BASE_URL}/api/v1/videos \\
  -H "X-API-Key: vv_live_..." \\
  -H "content-type: application/json" \\
  -d '{"idempotency_key":"order-123","product":{"name":"Tai nghe ABC"},"seconds":15,"aspect":"9:16"}'`;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <div className="flex items-center gap-2">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-grad-brand-soft">
            <KeyRound className="h-5 w-5 text-violet-300" />
          </span>
          <h1 className="font-display text-2xl font-bold text-ink-high lg:text-[32px]">API & Webhook</h1>
        </div>
        <p className="mt-1 text-ink-low">Tạo video bằng code. Tích hợp Vyra vào hệ thống của bạn.</p>
      </div>

      {/* API keys */}
      <GlassCard className="p-5">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-ink-low">
          <KeyRound className="h-4 w-4 text-violet-300" /> Khoá API
        </div>

        {newKey && (
          <div className="mb-3 rounded-xl border border-success/30 bg-success/[0.06] p-3">
            <p className="mb-1.5 text-xs text-success">Lưu lại ngay — khoá chỉ hiện 1 lần này:</p>
            <div className="flex items-center gap-2">
              <code className="flex-1 truncate rounded-lg bg-bg-base/60 px-3 py-2 font-mono text-xs text-ink-high">{newKey}</code>
              <Button size="sm" variant="glass" className="gap-1.5" onClick={() => copy(newKey, "key")}>
                {copied === "key" ? <Check className="h-4 w-4 text-success" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        )}

        <div className="flex gap-2">
          <input className={cn(inputCls, "flex-1")} value={keyName} onChange={(e) => setKeyName(e.target.value)}
                 placeholder="Tên khoá (vd: Tích hợp Shopee)" maxLength={120} />
          <Button variant="glass" className="gap-1.5" disabled={busy} onClick={createKey}>
            <Plus className="h-4 w-4 text-violet-300" /> Tạo khoá
          </Button>
        </div>

        <div className="mt-4 flex flex-col divide-y divide-white/[0.06]">
          {keys.isLoading ? (
            <Skeleton className="h-12 w-full" />
          ) : (keys.data ?? []).length === 0 ? (
            <p className="py-3 text-sm text-ink-low">Chưa có khoá nào.</p>
          ) : (
            (keys.data ?? []).map((k) => (
              <div key={k.id} className="flex items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium text-ink-high">{k.name || "Khoá"}</div>
                  <div className="font-mono text-xs text-ink-low">
                    {k.prefix}…{k.last_used_at ? " · đã dùng" : " · chưa dùng"}
                  </div>
                </div>
                <Button size="sm" variant="glass" className="gap-1.5" onClick={() => revokeKey(k.id)}>
                  <Trash2 className="h-3.5 w-3.5 text-danger" /> Thu hồi
                </Button>
              </div>
            ))
          )}
        </div>
      </GlassCard>

      {/* curl example */}
      <GlassCard className="p-5">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-ink-low">
          <Terminal className="h-4 w-4 text-violet-300" /> Ví dụ tạo video
        </div>
        <pre className="overflow-x-auto rounded-xl bg-bg-base/60 p-4 font-mono text-xs leading-relaxed text-ink-medium">{curl}</pre>
      </GlassCard>

      {/* webhooks */}
      <GlassCard className="p-5">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-ink-low">
          <Webhook className="h-4 w-4 text-violet-300" /> Webhook
        </div>
        <p className="mb-3 text-sm text-ink-low">
          Nhận thông báo khi video xong (READY/FAILED), payload ký HMAC qua header <code className="text-ink-medium">X-Vyra-Signature</code>.
        </p>

        {newSecret && (
          <div className="mb-3 rounded-xl border border-success/30 bg-success/[0.06] p-3">
            <p className="mb-1.5 text-xs text-success">Secret để verify chữ ký — chỉ hiện 1 lần:</p>
            <div className="flex items-center gap-2">
              <code className="flex-1 truncate rounded-lg bg-bg-base/60 px-3 py-2 font-mono text-xs text-ink-high">{newSecret}</code>
              <Button size="sm" variant="glass" className="gap-1.5" onClick={() => copy(newSecret, "secret")}>
                {copied === "secret" ? <Check className="h-4 w-4 text-success" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        )}

        <div className="flex gap-2">
          <input className={cn(inputCls, "flex-1")} value={hookUrl} onChange={(e) => setHookUrl(e.target.value)}
                 placeholder="https://hệ-thống-của-bạn.vn/webhook" />
          <Button variant="glass" className="gap-1.5" disabled={busy || !hookUrl.trim().startsWith("http")} onClick={createHook}>
            <Plus className="h-4 w-4 text-violet-300" /> Thêm
          </Button>
        </div>

        <div className="mt-4 flex flex-col divide-y divide-white/[0.06]">
          {hooks.isLoading ? (
            <Skeleton className="h-12 w-full" />
          ) : (hooks.data ?? []).length === 0 ? (
            <p className="py-3 text-sm text-ink-low">Chưa có webhook nào.</p>
          ) : (
            (hooks.data ?? []).map((h) => (
              <div key={h.id} className="flex items-center justify-between gap-3 py-3">
                <div className="min-w-0 truncate font-mono text-xs text-ink-medium">{h.url}</div>
                <Button size="sm" variant="glass" className="gap-1.5" onClick={() => deleteHook(h.id)}>
                  <Trash2 className="h-3.5 w-3.5 text-danger" /> Xoá
                </Button>
              </div>
            ))
          )}
        </div>
      </GlassCard>
    </div>
  );
}
