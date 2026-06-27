import Link from "next/link";
import { Logo } from "@/components/brand/logo";

/** Khung căn giữa cho các trang auth phụ (quên/đặt lại mật khẩu, xác minh email, lời mời). */
export function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mesh-bg grid min-h-dvh place-items-center px-4 py-10">
      <div className="w-full max-w-sm">
        <Link href="/" className="mb-8 inline-block">
          <Logo />
        </Link>
        <h1 className="text-2xl font-bold text-ink-high">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-ink-low">{subtitle}</p>}
        <div className="mt-6">{children}</div>
      </div>
    </div>
  );
}
