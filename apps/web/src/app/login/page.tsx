"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { Mail, Lock, User, AlertCircle, Loader2, ShieldCheck, Check } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Field, inputCls } from "@/components/ui/field";
import { FilmLabel } from "@/components/ui/cinematic";
import { registerLocal, loginLocal } from "@/lib/auth/local";
import { signInWithProvider, type OAuthProvider } from "@/lib/auth/oauth";

// "tạo mọi nội dung AI" — đa model, ảnh candid thật từ /showcase (không model nhựa).
// Hai cột trôi ngược chiều = một bức tường output, KHÔNG phải hero CineHero (bố cục riêng màn login).
const WALL_LEFT = ["/showcase/kol.jpg", "/showcase/lookbook.jpg", "/showcase/food.jpg", "/showcase/explainer.jpg"];
const WALL_RIGHT = ["/showcase/affiliate.jpg", "/showcase/trend.jpg", "/showcase/product.jpg", "/showcase/shortfilm.jpg"];

export default function LoginPage() {
  const t = useTranslations("login");
  const router = useRouter();

  // đồng bộ với ProofStrip trang chủ (không lệch "9 công cụ"). Chỉ dữ liệu THẬT.
  const STATS = [
    { v: "~60s", l: t("statPerVideo") },
    { v: "10+", l: t("statTools") },
    { v: "300", l: t("statCredits") },
  ];

  // điều người dùng tạo được — plain, cụ thể (không hype).
  const CAN_DO = [t("canDo1"), t("canDo2"), t("canDo3")];
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState<null | "form" | OAuthProvider>(null);
  const [error, setError] = useState<string | null>(null);

  // Quay về từ OAuth lỗi (/login?error=oauth) → báo cho người dùng.
  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("error") === "oauth") {
      setError(t("errorOauth"));
    }
  }, [t]);

  async function social(provider: OAuthProvider) {
    setLoading(provider);
    setError(null);
    try {
      await signInWithProvider(provider, nextTarget());
      // Thành công sẽ điều hướng sang provider; về lại đây nghĩa là có lỗi cấu hình.
    } catch (err) {
      setError(err instanceof Error ? err.message : t("errorGeneric"));
      setLoading(null);
    }
  }

  // Sau khi đăng nhập, quay lại ?next nếu là path nội bộ (chống open-redirect), mặc định /app.
  function nextTarget() {
    if (typeof window === "undefined") return "/app";
    const n = new URLSearchParams(window.location.search).get("next");
    return n && n.startsWith("/") && !n.startsWith("//") ? n : "/app";
  }

  // validate phía client trước khi gọi API — báo lỗi tiếng Việt rõ ràng, hợp lệ cả 2 chế độ.
  function validate(): string | null {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) return t("errorEmailInvalid");
    if (password.length < 8) return t("errorPasswordShort");
    if (mode === "register" && name.trim().length < 2) return t("errorNameRequired");
    return null;
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const invalid = validate();
    if (invalid) {
      setError(invalid);
      return;
    }
    setLoading("form");
    setError(null);
    try {
      if (mode === "register") await registerLocal(email, password, name);
      else await loginLocal(email, password);
      router.push(nextTarget());
    } catch (err) {
      setError(err instanceof Error ? err.message : t("errorGeneric"));
      setLoading(null);
    }
  }


  return (
    <div className="grid min-h-dvh lg:grid-cols-[1.05fr_1fr]">
      {/* ── LEFT — TƯỜNG OUTPUT (signature riêng màn login) ─────────────────
          hai cột ảnh candid trôi ngược chiều, scrim brand, value-prop dồn đáy.
          Ẩn trên mobile. Khác hẳn CineHero/bento của các màn khác. */}
      <div className="relative hidden overflow-hidden bg-bg-surface lg:block">
        {/* lưới ảnh trôi — nền chuyển động nhẹ, candid thật, không stock.
            Mask fade TRÁI→PHẢI: cột sau logo+chữ tan biến (hết "mép ảnh ghép lỗi"),
            chỉ giữ gallery bên phải. */}
        {/* fade ảnh tan mềm ở MỌI mép bằng 2 mask 1-TRỤC LỒNG NHAU (KHÔNG dùng
            mask-composite: intersect — cú pháp đó vỡ trên Chrome, để lại mép thẻ cứng).
            Ngoài = fade dọc (đỉnh/đáy); trong = fade ngang (trái→phải, ảnh tan sau chữ). */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.32] blur-[1.5px]"
          style={{
            maskImage: "linear-gradient(to bottom, transparent 0%, #000 22%, #000 80%, transparent 100%)",
            WebkitMaskImage: "linear-gradient(to bottom, transparent 0%, #000 22%, #000 80%, transparent 100%)",
          }}
        >
          <div
            className="flex h-full justify-end gap-3 pr-6"
            style={{
              maskImage: "linear-gradient(to right, transparent 0%, transparent 30%, #000 72%)",
              WebkitMaskImage: "linear-gradient(to right, transparent 0%, transparent 30%, #000 72%)",
            }}
          >
            <DriftColumn images={WALL_LEFT} dir="up" />
            <DriftColumn images={WALL_RIGHT} dir="down" className="hidden xl:flex" />
          </div>
        </div>

        {/* scrim brand: tối từ trái sang để chữ luôn đọc rõ + đáy đậm cho cụm value-prop */}
        <div className="absolute inset-0 bg-gradient-to-r from-bg-surface via-bg-surface/85 to-bg-surface/30" />
        <div className="absolute inset-0 bg-gradient-to-t from-bg-surface via-bg-surface/40 to-transparent" />
        {/* 1 vầng glow violet duy nhất (đúng luật: 1 glow/màn). Kéo LÊN qua mép trên
            (-top-24) để glow chạm hẳn góc trên-trái, KHÔNG để hở dải đen ở đỉnh. */}
        <div className="glow-radial pointer-events-none absolute -left-24 -top-24 h-[480px] w-[480px]" />

        {/* nội dung trái: logo trên — value-prop dưới (bất đối xứng, dồn đáy) */}
        <div className="relative flex h-full flex-col justify-between p-10 xl:p-12">
          {/* logo bấm được → về trang chủ (trước đây trơ, user kẹt ở login) */}
          <Link href="/" aria-label="Về trang chủ" className="w-fit">
            <Logo />
          </Link>

          <div className="max-w-md">
            <FilmLabel>{t("studioLabel")}</FilmLabel>
            <h1 className="mt-4 font-display text-[clamp(2rem,3.2vw,2.9rem)] font-extrabold leading-[1.08] tracking-[-0.02em] text-ink-high">
              {t("heroTitleLine1")}
              <br />
              <span className="text-gradient">{t("heroTitleLine2")}</span>
            </h1>
            <p className="mt-4 max-w-sm leading-relaxed text-ink-medium">
              {t("heroSubtitle")}
            </p>

            <ul className="mt-6 flex flex-col gap-2.5">
              {CAN_DO.map((c) => (
                <li key={c} className="flex items-center gap-2.5 text-sm text-ink-medium">
                  <span className="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-violet-500/15 text-violet-300 ring-1 ring-violet-400/25">
                    <Check className="h-3 w-3" strokeWidth={3} />
                  </span>
                  {c}
                </li>
              ))}
            </ul>

            <div className="mt-8 flex gap-8 border-t border-white/[0.06] pt-6">
              {STATS.map((s) => (
                <div key={s.l}>
                  <div className="font-numeric text-3xl font-bold text-ink-high">{s.v}</div>
                  <div className="mt-0.5 text-sm text-ink-low">{s.l}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2 text-sm text-ink-low">
            <span className="h-2 w-2 rounded-full bg-success shadow-glow-success" />
            {t("transparentPricing")}
          </div>
        </div>
      </div>

      {/* ── RIGHT — thẻ auth nổi trên mesh ─────────────────────────────────── */}
      <div className="relative grid place-items-center overflow-hidden mesh-bg px-4 py-10">
        <Link href="/" className="absolute left-6 top-6 lg:hidden">
          <Logo />
        </Link>
        {/* nút trở về trang chủ (desktop) — user không bị kẹt ở màn đăng nhập */}
        <Link
          href="/"
          className="absolute right-6 top-6 hidden items-center gap-1.5 text-sm text-ink-low transition-colors hover:text-ink-medium lg:flex"
        >
          <span aria-hidden>←</span> Trang chủ
        </Link>

        {/* thẻ kính viền-gradient — bản sắc Vyra (KHÔNG bare column như cũ) */}
        <div className="w-full max-w-sm rounded-3xl glass-bordered p-7 sm:p-8">
          <FilmLabel className="mb-4">{mode === "register" ? t("cardLabelRegister") : t("cardLabelLogin")}</FilmLabel>
          <h2 className="font-display text-2xl font-bold text-ink-high">
            {mode === "register" ? t("cardTitleRegister") : t("cardTitleLogin")}
          </h2>
          <p className="mt-1 text-sm text-ink-low">
            {mode === "register" ? t("cardSubtitleRegister") : t("cardSubtitleLogin")}
          </p>

          <div className="mt-6 grid grid-cols-2 gap-1 rounded-xl border border-white/10 bg-white/[0.02] p-1">
            {(["login", "register"] as const).map((m) => (
              <button
                key={m}
                onClick={() => {
                  setMode(m);
                  setError(null);
                }}
                aria-pressed={mode === m}
                className={`rounded-lg py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50 ${
                  mode === m ? "bg-violet-500/20 text-ink-high shadow-glow-sm" : "text-ink-low hover:text-ink-medium"
                }`}
              >
                {m === "login" ? t("tabLogin") : t("tabRegister")}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="mt-5 flex flex-col gap-4">
            {mode === "register" && (
              <Field label={t("nameLabel")}>
                <div className="relative">
                  <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-low" />
                  <input className={`${inputCls} pl-9`} value={name} onChange={(e) => setName(e.target.value)} placeholder={t("namePlaceholder")} />
                </div>
              </Field>
            )}
            <Field label={t("emailLabel")}>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-low" />
                <input type="email" required className={`${inputCls} pl-9`} value={email} onChange={(e) => setEmail(e.target.value)} placeholder="ban@email.com" />
              </div>
            </Field>
            <Field label={t("passwordLabel")}>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-low" />
                <input type="password" required minLength={8} className={`${inputCls} pl-9`} value={password} onChange={(e) => setPassword(e.target.value)} placeholder={t("passwordPlaceholder")} />
              </div>
            </Field>

            {mode === "login" && (
              <Link
                href="/forgot-password"
                className="-mt-2 self-end text-xs text-violet-300 transition-colors hover:text-violet-200"
              >
                {t("forgotPassword")}
              </Link>
            )}

            {error && (
              <div className="flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/[0.1] p-3 text-sm text-danger">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <Button type="submit" size="lg" disabled={loading !== null}>
              {loading === "form" ? <Loader2 className="h-4 w-4 animate-spin" /> : mode === "register" ? t("submitRegister") : t("submitLogin")}
            </Button>
          </form>

          <div className="my-5 flex items-center gap-3 text-[11px] uppercase tracking-[0.2em] text-ink-disabled">
            <span className="h-px flex-1 bg-white/[0.08]" />
            {t("orDivider")}
            <span className="h-px flex-1 bg-white/[0.08]" />
          </div>
          <div className="flex flex-col gap-2.5">
            <Button variant="glass" size="lg" className="w-full gap-2.5" disabled={loading !== null} onClick={() => social("google")}>
              {loading === "google" ? <Loader2 className="h-4 w-4 animate-spin" /> : <GoogleIcon />}
              {t("continueGoogle")}
            </Button>
            <Button variant="glass" size="lg" className="w-full gap-2.5" disabled={loading !== null} onClick={() => social("facebook")}>
              {loading === "facebook" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FacebookIcon />}
              {t("continueFacebook")}
            </Button>
          </div>

          <p className="mt-6 flex items-center justify-center gap-1.5 text-[11px] text-ink-disabled">
            <ShieldCheck className="h-3.5 w-3.5" /> {t("tlsSecurity")}
          </p>
        </div>
      </div>
    </div>
  );
}

/** Một cột ảnh candid trôi chậm theo phương dọc (lặp vô hạn). reduced-motion: dừng yên.
 *  Lặp ảnh 2 lần để vòng -50% liền mạch. Chỉ trang trí (aria-hidden, pointer-events-none). */
function DriftColumn({
  images,
  dir,
  className = "",
}: {
  images: string[];
  dir: "up" | "down";
  className?: string;
}) {
  const reduce = useReducedMotion();
  const loop = [...images, ...images];
  const from = dir === "up" ? "0%" : "-50%";
  const to = dir === "up" ? "-50%" : "0%";
  return (
    <div className={`relative w-[220px] shrink-0 overflow-hidden ${className}`} aria-hidden>
      <motion.div
        className="flex flex-col gap-4 will-change-transform"
        initial={false}
        animate={reduce ? undefined : { y: [from, to] }}
        transition={{ duration: 46, ease: "linear", repeat: Infinity }}
      >
        {loop.map((src, i) => (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            key={`${src}-${i}`}
            src={src}
            alt=""
            loading="lazy"
            className="h-[280px] w-full rounded-[20px] object-cover"
          />
        ))}
      </motion.div>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" aria-hidden>
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.27-4.74 3.27-8.1Z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23Z" />
      <path fill="#FBBC05" d="M5.84 14.1a6.6 6.6 0 0 1 0-4.2V7.06H2.18a11 11 0 0 0 0 9.88l3.66-2.84Z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1A11 11 0 0 0 2.18 7.06l3.66 2.84C6.71 7.3 9.14 5.38 12 5.38Z" />
    </svg>
  );
}

function FacebookIcon() {
  return (
    <svg className="h-[18px] w-[18px]" viewBox="0 0 24 24" aria-hidden>
      <path fill="#1877F2" d="M24 12a12 12 0 1 0-13.88 11.85v-8.38H7.08V12h3.04V9.36c0-3 1.79-4.67 4.53-4.67 1.31 0 2.68.24 2.68.24v2.95h-1.51c-1.49 0-1.95.92-1.95 1.87V12h3.32l-.53 3.47h-2.79v8.38A12 12 0 0 0 24 12Z" />
    </svg>
  );
}
