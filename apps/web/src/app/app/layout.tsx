import { AuthGate } from "@/components/shell/auth-gate";
import { SiteHeader } from "@/components/marketing/site-header";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGate>
      <div className="relative min-h-dvh mesh-bg">
        <SiteHeader authed />
        <main className="mx-auto w-full max-w-6xl overflow-x-clip px-4 pb-20 pt-28 lg:px-8">{children}</main>
      </div>
    </AuthGate>
  );
}
