import { Skeleton } from "@/components/ui/skeleton";

export function ReportsSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <Skeleton className="h-72 w-full rounded-3xl" />
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <Skeleton className="h-52 w-full rounded-2xl" />
        <Skeleton className="h-52 w-full rounded-2xl" />
      </div>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <Skeleton className="h-36 w-full rounded-2xl" />
        <Skeleton className="h-36 w-full rounded-2xl" />
      </div>
    </div>
  );
}
