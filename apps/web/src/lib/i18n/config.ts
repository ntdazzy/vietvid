// i18n không-routing: locale theo cookie 'NEXT_LOCALE', vi mặc định.
// Không đổi cấu trúc route — chỉ đọc cookie ở server và truyền messages xuống client.

export const LOCALES = ["vi", "en"] as const;
export type Locale = (typeof LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "vi";
export const LOCALE_COOKIE = "NEXT_LOCALE";

export function isLocale(value: string | undefined | null): value is Locale {
  return value === "vi" || value === "en";
}
