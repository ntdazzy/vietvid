"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { KeyRound, Webhook, Copy, Check, Trash2, Plus, ShieldCheck, Radio } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { API_BASE_URL } from "@/lib/config";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { inputCls } from "@/components/ui/field";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { ACCENTS } from "@/lib/accents";
import { cn } from "@/lib/utils/cn";

const A = ACCENTS.cyan;

export default function ApiPage() {
  const t = useTranslations("apipage");
  const qc = useQueryClient();
  const keys = useQuery({ queryKey: ["api-keys"], queryFn: api.apiKeys });
  const hooks = useQuery({ queryKey: ["webhooks"], queryFn: api.webhooks });

  const [keyName, setKeyName] = useState("");
  const [newKey, setNewKey] = useState<string | null>(null);
  const [hookUrl, setHookUrl] = useState("");
  const [newSecret, setNewSecret] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const [lang, setLang] = useState<"curl" | "node">("curl");

  function copy(text: string, tag: string) {
    navigator.clipboard.writeText(text);
    setCopied(tag);
    setTimeout(() => setCopied(null), 1500);
  }

  async function createKey() {
    setBusy(true);
    try {
      const r = await api.createApiKey(keyName.trim() || t("defaultKeyName"));
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

  const node = `const res = await fetch("${API_BASE_URL}/api/v1/videos", {
  method: "POST",
  headers: {
    "X-API-Key": "vv_live_...",
    "content-type": "application/json",
  },
  body: JSON.stringify({
    idempotency_key: "order-123",
    product: { name: "Tai nghe ABC" },
    seconds: 15,
    aspect: "9:16",
  }),
});
const job = await res.json();`;

  const snippet = lang === "curl" ? curl : node;

  return (
    <div className="flex flex-col gap-10">
      {/* ─── HERO SPLIT — pitch trái + terminal panel phải (signature: IDE / dev console) ─── */}
      <Reveal>
        <section className="relative overflow-hidden rounded-3xl glass-bordered">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/bg/desk.jpg" alt="" className="absolute inset-0 h-full w-full object-cover opacity-[0.12]" />
          <div className="absolute inset-0 bg-gradient-to-br from-bg-base via-bg-base/95 to-bg-base/70" />
          <div
            className="pointer-events-none absolute -right-20 -top-24 h-72 w-72 rounded-full blur-3xl"
            style={{ background: A.glow }}
          />
          <div className="relative grid gap-8 p-6 sm:p-9 lg:grid-cols-[1.05fr_1.25fr] lg:items-center lg:gap-10 lg:p-10">
            {/* trái — pitch */}
            <div>
              <FilmLabel>{t("heroLabel")}</FilmLabel>
              <h1 className="mt-4 font-display text-3xl font-extrabold leading-[1.05] text-ink-high sm:text-4xl lg:text-[46px]">
                {t.rich("heroTitle", { grad: (c) => <span className={A.text}>{c}</span> })}
              </h1>
              <p className="mt-4 max-w-md text-ink-medium">
                {t("heroDesc")}
              </p>
              <div className="mt-6 flex flex-wrap items-center gap-2.5">
                <span className={cn("inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 font-mono text-xs", A.chip)}>
                  <span className="rounded bg-cyan-400/20 px-1.5 py-0.5 font-bold">POST</span>
                  /api/v1/videos
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-2.5 py-1 text-xs text-ink-low">
                  <ShieldCheck className="h-3.5 w-3.5 text-cyan-300" /> {t("authByApiKey")}
                </span>
              </div>
            </div>

            {/* phải — terminal panel với tab code + copy */}
            <div className="min-w-0 overflow-hidden rounded-2xl border border-white/10 bg-[#0a0e17]/80 shadow-2xl backdrop-blur">
              <div className="flex items-center gap-2 border-b border-white/[0.07] px-4 py-2.5">
                <span className="flex gap-1.5" aria-hidden>
                  <span className="h-2.5 w-2.5 rounded-full bg-rose-400/70" />
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-400/70" />
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/70" />
                </span>
                <div className="ml-2 flex gap-1">
                  {(["curl", "node"] as const).map((l) => (
                    <button
                      key={l}
                      onClick={() => setLang(l)}
                      aria-pressed={lang === l}
                      className={cn(
                        "rounded-md px-2.5 py-1 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/40",
                        lang === l ? "bg-cyan-400/15 text-cyan-200" : "text-ink-low hover:text-ink-medium",
                      )}
                    >
                      {l === "curl" ? "cURL" : "Node.js"}
                    </button>
                  ))}
                </div>
                <button
                  onClick={() => copy(snippet, "snippet")}
                  aria-label={t("copyCodeAria")}
                  className="ml-auto inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs text-ink-low transition-colors hover:text-ink-high focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/40"
                >
                  {copied === "snippet" ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied === "snippet" ? t("copied") : t("copy")}
                </button>
              </div>
              <pre className="overflow-x-auto p-4 font-mono text-[12.5px] leading-relaxed text-cyan-100/90 sm:text-xs">
                <code>{snippet}</code>
              </pre>
            </div>
          </div>
        </section>
      </Reveal>

      {/* ─── BENTO bất đối xứng: Khoá API (rộng) | Webhook (hẹp) ─── */}
      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        {/* ── VAULT — quản lý khoá API ── */}
        <Reveal delay={0.05}>
          <section className="relative flex h-full flex-col overflow-hidden rounded-2xl glass-bordered p-5 sm:p-6">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className={cn("grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br ring-1", A.tile, A.ring)}>
                  <KeyRound className={cn("h-5 w-5", A.icon)} />
                </span>
                <div>
                  <FilmLabel dot={false}>{t("accessKeysLabel")}</FilmLabel>
                  <div className="mt-0.5 font-display text-lg font-bold text-ink-high">{t("apiKeys")}</div>
                </div>
              </div>
              <span className="font-numeric text-sm tabular text-ink-low">
                {keys.isLoading ? "—" : t("keysCount", { count: keys.data?.length ?? 0 })}
              </span>
            </div>

            {newKey && (
              <div className="mt-4 rounded-xl border border-cyan-400/30 bg-cyan-400/[0.06] p-3">
                <p className="mb-1.5 flex items-center gap-1.5 text-xs text-cyan-200">
                  <ShieldCheck className="h-3.5 w-3.5" /> {t("keyOnceWarning")}
                </p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 truncate rounded-lg bg-bg-base/60 px-3 py-2 font-mono text-xs text-ink-high">{newKey}</code>
                  <Button size="sm" variant="glass" className="gap-1.5" aria-label={t("copyKeyAria")} onClick={() => copy(newKey, "key")}>
                    {copied === "key" ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            )}

            <div className="mt-4 flex gap-2">
              <input
                className={cn(inputCls, "flex-1")}
                value={keyName}
                onChange={(e) => setKeyName(e.target.value)}
                placeholder={t("keyNamePlaceholder")}
                maxLength={120}
              />
              <Button variant="glass" className="gap-1.5" disabled={busy} onClick={createKey}>
                <Plus className={cn("h-4 w-4", A.icon)} /> {t("createKey")}
              </Button>
            </div>

            <div className="mt-4 flex flex-1 flex-col gap-2">
              {keys.isLoading ? (
                <>
                  <Skeleton className="h-14 w-full rounded-xl" />
                  <Skeleton className="h-14 w-full rounded-xl" />
                </>
              ) : (keys.data ?? []).length === 0 ? (
                <div className="grid flex-1 place-items-center rounded-xl border border-dashed border-white/10 py-10 text-center">
                  <div>
                    <KeyRound className="mx-auto h-7 w-7 text-ink-low" />
                    <p className="mt-2 text-sm text-ink-low">{t("keysEmpty")}</p>
                  </div>
                </div>
              ) : (
                (keys.data ?? []).map((k) => (
                  <div
                    key={k.id}
                    className="group flex items-center justify-between gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] px-4 py-3 transition-colors hover:border-cyan-400/20"
                  >
                    <div className="flex min-w-0 items-center gap-3">
                      <span
                        className={cn(
                          "h-2 w-2 shrink-0 rounded-full",
                          k.last_used_at ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]" : "bg-white/20",
                        )}
                        aria-hidden
                      />
                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium text-ink-high">{k.name || t("keyFallback")}</div>
                        <div className="font-mono text-xs text-ink-low">
                          {k.prefix}… · {k.last_used_at ? t("used") : t("unused")}
                        </div>
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="glass"
                      className="gap-1.5 opacity-70 transition-opacity group-hover:opacity-100"
                      aria-label={t("revokeKeyAria", { name: k.name || t("keyFallback") })}
                      onClick={() => revokeKey(k.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5 text-danger" /> {t("revoke")}
                    </Button>
                  </div>
                ))
              )}
            </div>
          </section>
        </Reveal>

        {/* ── PIPE — webhook (đường ống sự kiện) ── */}
        <Reveal delay={0.1}>
          <section className="relative flex h-full flex-col overflow-hidden rounded-2xl glass-bordered p-5 sm:p-6">
            <div className="flex items-center gap-3">
              <span className={cn("grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br ring-1", A.tile, A.ring)}>
                <Webhook className={cn("h-5 w-5", A.icon)} />
              </span>
              <div>
                <FilmLabel dot={false}>{t("eventPipeLabel")}</FilmLabel>
                <div className="mt-0.5 font-display text-lg font-bold text-ink-high">{t("webhook")}</div>
              </div>
            </div>

            <div className="mt-4 flex items-start gap-2 rounded-xl border border-white/[0.06] bg-white/[0.02] p-3">
              <Radio className="mt-0.5 h-4 w-4 shrink-0 text-cyan-300" />
              <p className="text-xs leading-relaxed text-ink-low">
                {t.rich("webhookDesc", {
                  code: () => (
                    <code className="rounded bg-bg-base/60 px-1 py-0.5 font-mono text-cyan-200">X-Vyra-Signature</code>
                  ),
                })}
              </p>
            </div>

            {newSecret && (
              <div className="mt-3 rounded-xl border border-cyan-400/30 bg-cyan-400/[0.06] p-3">
                <p className="mb-1.5 flex items-center gap-1.5 text-xs text-cyan-200">
                  <ShieldCheck className="h-3.5 w-3.5" /> {t("secretOnceWarning")}
                </p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 truncate rounded-lg bg-bg-base/60 px-3 py-2 font-mono text-xs text-ink-high">{newSecret}</code>
                  <Button size="sm" variant="glass" className="gap-1.5" aria-label={t("copySecretAria")} onClick={() => copy(newSecret, "secret")}>
                    {copied === "secret" ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            )}

            <div className="mt-3 flex flex-col gap-2 sm:flex-row">
              <input
                className={cn(inputCls, "flex-1")}
                value={hookUrl}
                onChange={(e) => setHookUrl(e.target.value)}
                placeholder={t("webhookUrlPlaceholder")}
              />
              <Button
                variant="glass"
                className="gap-1.5"
                disabled={busy || !hookUrl.trim().startsWith("http")}
                onClick={createHook}
              >
                <Plus className={cn("h-4 w-4", A.icon)} /> {t("add")}
              </Button>
            </div>

            <div className="mt-4 flex flex-1 flex-col gap-2">
              {hooks.isLoading ? (
                <Skeleton className="h-12 w-full rounded-xl" />
              ) : (hooks.data ?? []).length === 0 ? (
                <div className="grid flex-1 place-items-center rounded-xl border border-dashed border-white/10 py-8 text-center">
                  <div>
                    <Webhook className="mx-auto h-7 w-7 text-ink-low" />
                    <p className="mt-2 text-sm text-ink-low">{t("webhooksEmpty")}</p>
                  </div>
                </div>
              ) : (
                (hooks.data ?? []).map((h) => (
                  <div
                    key={h.id}
                    className="group flex items-center justify-between gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] px-4 py-3 transition-colors hover:border-cyan-400/20"
                  >
                    <div className="flex min-w-0 items-center gap-2">
                      <span
                        className={cn(
                          "h-2 w-2 shrink-0 rounded-full",
                          h.active ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]" : "bg-white/20",
                        )}
                        aria-hidden
                      />
                      <span className="min-w-0 truncate font-mono text-xs text-ink-medium">{h.url}</span>
                    </div>
                    <Button
                      size="sm"
                      variant="glass"
                      className="gap-1.5 opacity-70 transition-opacity group-hover:opacity-100"
                      aria-label={t("deleteWebhookAria")}
                      onClick={() => deleteHook(h.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5 text-danger" /> {t("delete")}
                    </Button>
                  </div>
                ))
              )}
            </div>
          </section>
        </Reveal>
      </div>
    </div>
  );
}
