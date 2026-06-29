"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { ReactNode } from "react";
import { ACCENTS, type Accent } from "@/lib/accents";
import { cn } from "@/lib/utils/cn";

/**
 * Primitive premium DÙNG CHUNG cho Vyra — bản sắc RIÊNG (KHÔNG nhái autovis):
 * brand tím + glass viền-gradient + eyebrow thanh-gradient. ĐÃ BỎ "khung ngắm" (viewfinder)
 * và nhãn "REC/TAKE/SCENE" vì đó là dấu hiệu của autovis.
 */

/** Đã bỏ khung-ngắm 4 góc (viewfinder = dấu hiệu autovis). Giữ export để không vỡ import; render rỗng. */
export function CornerFrame(_props: { className?: string; color?: string; inset?: string }) {
  return null;
}

/** Eyebrow Vyra: thanh gradient tím nhỏ + nhãn in hoa giãn chữ (sans). KHÔNG chấm đỏ REC, KHÔNG mono. */
export function FilmLabel({
  children,
  dot = true,
  className,
}: {
  children: ReactNode;
  dot?: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2.5 text-[11px] font-semibold uppercase tracking-[0.2em] text-ink-low",
        className,
      )}
    >
      {dot && <span className="h-[3px] w-5 rounded-full bg-grad-brand" />}
      {children}
    </span>
  );
}

/**
 * Hero premium full-bleed: nền media + scrim brand + tiêu đề lớn dồn đáy. `status` phải là
 * THÔNG TIN THẬT (không số bịa). Bản sắc Vyra: glass viền-gradient + 1 vầng glow accent + eyebrow.
 */
export function CineHero({
  accent = "violet",
  bg,
  label,
  status,
  eyebrow,
  title,
  sub,
  actions,
  children,
}: {
  accent?: Accent;
  bg?: string;
  label?: ReactNode;
  status?: ReactNode;
  eyebrow?: ReactNode;
  title: ReactNode;
  sub?: ReactNode;
  actions?: ReactNode;
  children?: ReactNode;
}) {
  const a = ACCENTS[accent];
  return (
    <section className="relative overflow-hidden rounded-3xl glass-bordered">
      {bg && (
        <>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={bg} alt="" className="absolute inset-0 h-full w-full animate-kenburns object-cover opacity-35" />
          <div className="absolute inset-0 bg-gradient-to-r from-bg-base via-bg-base/92 to-bg-base/35" />
          <div className="absolute inset-0 bg-gradient-to-t from-bg-base via-bg-base/20 to-transparent" />
        </>
      )}
      <div
        className="pointer-events-none absolute -top-24 left-1/3 h-64 w-64 rounded-full blur-3xl"
        style={{ background: a.glow }}
      />
      <div className="relative flex min-h-[300px] flex-col justify-between gap-8 p-6 sm:min-h-[360px] sm:p-9 lg:min-h-[420px] lg:p-10">
        <div className="flex items-center justify-between gap-3">
          {label && <FilmLabel>{label}</FilmLabel>}
          {status && (
            <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-low">{status}</span>
          )}
        </div>
        <div className="max-w-2xl">
          {eyebrow && (
            <span className={cn("text-xs font-semibold uppercase tracking-[0.2em]", a.text)}>{eyebrow}</span>
          )}
          <h1 className="mt-3 font-display text-3xl font-extrabold leading-[1.05] text-ink-high sm:text-4xl lg:text-[52px]">
            {title}
          </h1>
          {sub && <p className="mt-3 max-w-xl text-ink-medium sm:text-lg">{sub}</p>}
          {actions && <div className="mt-6 flex flex-wrap items-center gap-3">{actions}</div>}
          {children && <div className="mt-6">{children}</div>}
        </div>
      </div>
    </section>
  );
}

/**
 * Thẻ nội dung có ẢNH: media + scrim + chip nhãn (accent) + tiêu đề/mô tả. Hover: nhấc + glow +
 * zoom ảnh + ring accent. KHÔNG khung-ngắm. Dùng cho launchpad/hub/genre.
 */
export function ContentCard({
  href,
  image,
  accent = "violet",
  label,
  title,
  desc,
  badge,
}: {
  href: string;
  image: string;
  accent?: Accent;
  label?: ReactNode;
  title: string;
  desc?: string;
  badge?: string;
}) {
  const a = ACCENTS[accent];
  return (
    <Link
      href={href}
      className={cn(
        "group relative flex flex-col overflow-hidden rounded-2xl glass-bordered transition-all duration-200 hover:-translate-y-1 hover:shadow-glow-sm hover:ring-1",
        a.ring,
      )}
    >
      <div className="relative aspect-[16/10] overflow-hidden">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={image}
          alt=""
          loading="lazy"
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.05]"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-bg-surface via-bg-surface/30 to-transparent" />
        {badge && (
          <span className={cn("absolute left-3 top-3 rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide", a.chip)}>
            {badge}
          </span>
        )}
        {label && (
          <span className={cn("absolute bottom-2.5 left-3 text-[11px] font-semibold uppercase tracking-[0.16em]", a.text)}>{label}</span>
        )}
      </div>
      <div className="flex items-start gap-2 p-4">
        <div className="min-w-0">
          <div className="font-display font-semibold text-ink-high">{title}</div>
          {desc && <p className="mt-0.5 text-sm leading-snug text-ink-low">{desc}</p>}
        </div>
        <ArrowRight className={cn("ml-auto mt-0.5 h-4 w-4 shrink-0 transition group-hover:translate-x-0.5", a.icon)} />
      </div>
    </Link>
  );
}
