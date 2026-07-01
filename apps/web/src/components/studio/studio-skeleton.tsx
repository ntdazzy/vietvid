import { cn } from "@/lib/utils/cn";

// Khung-xương khớp bố cục STUDIO (rail trái + nội dung) — hiện khi màn đang tải (Next streaming).
// KHÔNG spinner tròn: khối mờ đập nhịp giống hình dáng thật → mắt biết cái gì sắp hiện ở đâu.
// animate-pulse là CSS nên tự đứng yên khi prefers-reduced-motion (globals kill).

function Block({ className }: { className?: string }) {
  return <div className={cn("rounded-2xl bg-white/[0.04]", className)} />;
}

/** Rail trái giả — 7 ô công cụ. */
function RailBones() {
  return (
    <div className="sticky top-28 hidden h-[calc(100dvh-9rem)] w-[78px] shrink-0 flex-col gap-2 rounded-2xl bg-white/[0.03] p-2 lg:flex">
      {Array.from({ length: 7 }).map((_, i) => (
        <div key={i} className="h-12 rounded-xl bg-white/[0.05]" />
      ))}
    </div>
  );
}

type Variant = "launchpad" | "workbench" | "list" | "hub";

/** variant:
 *  - launchpad: hero banner + lưới thẻ thể loại (màn Tạo video)
 *  - workbench: khung xem lớn + panel công cụ phải (Ảnh)
 *  - list: cột nhập + danh sách lựa chọn phải (Âm thanh)
 *  - hub: hero + hàng ô nhanh + lưới (Dự án) */
export function StudioSkeleton({ variant = "workbench" }: { variant?: Variant }) {
  return (
    <div className="flex animate-pulse gap-5">
      <RailBones />
      <div className="min-w-0 flex-1">
        {variant === "launchpad" && (
          <div className="flex flex-col gap-6">
            <Block className="h-[168px]" />
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => <Block key={i} className="h-52" />)}
            </div>
          </div>
        )}
        {variant === "workbench" && (
          <div className="flex flex-col gap-6">
            <Block className="h-[168px]" />
            <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
              <Block className="h-[420px]" />
              <div className="flex flex-col gap-4">
                <Block className="h-32" />
                <Block className="h-24" />
                <Block className="h-40" />
              </div>
            </div>
          </div>
        )}
        {variant === "list" && (
          <div className="flex flex-col gap-6">
            <Block className="h-[120px]" />
            <div className="grid gap-6 lg:grid-cols-2">
              <Block className="h-[440px]" />
              <div className="flex flex-col gap-3">
                {Array.from({ length: 6 }).map((_, i) => <Block key={i} className="h-16" />)}
              </div>
            </div>
          </div>
        )}
        {variant === "hub" && (
          <div className="flex flex-col gap-8">
            <Block className="h-[200px] rounded-3xl" />
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
              {Array.from({ length: 6 }).map((_, i) => <Block key={i} className="h-28" />)}
            </div>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              {Array.from({ length: 8 }).map((_, i) => <Block key={i} className="aspect-[9/16]" />)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
