"use client";

import { useTranslations } from "next-intl";
import { UserPlus, Mail, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Field, inputCls } from "@/components/ui/field";
import { Reveal } from "@/components/marketing/reveal";
import { ACCENTS } from "@/lib/accents";
import { cn } from "@/lib/utils/cn";

const A = ACCENTS.sky;

/** Cột mời thành viên — form email + trạng thái gửi (sticky trên desktop). */
export function InviteForm({
  email,
  onEmailChange,
  busy,
  msg,
  onSubmit,
}: {
  email: string;
  onEmailChange: (value: string) => void;
  busy: boolean;
  msg: { kind: "ok" | "err"; text: string } | null;
  onSubmit: (e: React.FormEvent) => void;
}) {
  const t = useTranslations("team");
  return (
    <Reveal delay={0.05}>
      <section className="relative overflow-hidden rounded-3xl glass-bordered p-5 sm:p-6">
        <div
          className="pointer-events-none absolute -left-8 -top-10 h-32 w-32 rounded-full blur-3xl"
          style={{ background: A.glow }}
        />
        <div className="relative">
          <div className="mb-1 flex items-center gap-2">
            <span className={cn("grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br ring-1", A.tile, A.ring)}>
              <UserPlus className={cn("h-5 w-5", A.icon)} />
            </span>
            <div className="font-display font-semibold text-ink-high">{t("inviteTitle")}</div>
          </div>
          <p className="mb-4 text-sm text-ink-low">
            {t("inviteDescription")}
          </p>
          <form onSubmit={onSubmit} className="flex flex-col gap-3">
            <Field label={t("emailLabel")}>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-low" />
                <input
                  type="email"
                  required
                  className={`${inputCls} pl-9`}
                  value={email}
                  onChange={(e) => onEmailChange(e.target.value)}
                  placeholder={t("emailPlaceholder")}
                />
              </div>
            </Field>
            <Button type="submit" disabled={busy} className="w-full gap-2">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />}
              {t("sendInvite")}
            </Button>
          </form>
          {msg && (
            <p
              className={cn(
                "mt-3 rounded-lg px-3 py-2 text-sm",
                msg.kind === "ok"
                  ? "bg-success/[0.08] text-success"
                  : "bg-danger/[0.08] text-danger",
              )}
              role="status"
            >
              {msg.text}
            </p>
          )}
        </div>
      </section>
    </Reveal>
  );
}
