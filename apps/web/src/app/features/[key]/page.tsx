import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { FEATURE_PAGES, FEATURE_PAGE_KEYS } from "@/lib/feature-pages";
import { FeatureShowcase } from "@/components/marketing/feature-showcase";

export function generateStaticParams() {
  return FEATURE_PAGE_KEYS.map((key) => ({ key }));
}

export function generateMetadata({ params }: { params: { key: string } }): Metadata {
  const p = FEATURE_PAGES[params.key];
  if (!p) return { title: "Tính năng — Vyra" };
  return { title: `${p.title.replace("|", " ")} — Vyra`, description: p.sub };
}

export default function FeaturePageRoute({ params }: { params: { key: string } }) {
  const page = FEATURE_PAGES[params.key];
  if (!page) notFound();
  return <FeatureShowcase page={page} />;
}
