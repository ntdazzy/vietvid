import { cookies } from "next/headers";
import type { AbstractIntlMessages } from "next-intl";
import { DEFAULT_LOCALE, LOCALE_COOKIE, isLocale, type Locale } from "./config";

// Đọc locale từ cookie ở server (RSC). Mặc định 'vi' nếu chưa đặt / giá trị lạ.
export function getLocale(): Locale {
  const value = cookies().get(LOCALE_COOKIE)?.value;
  return isLocale(value) ? value : DEFAULT_LOCALE;
}

// Load messages JSON tương ứng locale. Lỗi/khuyết → fallback 'vi'.
export async function getMessages(locale: Locale): Promise<AbstractIntlMessages> {
  try {
    return (await import(`../../../messages/${locale}.json`)).default as AbstractIntlMessages;
  } catch {
    return (await import(`../../../messages/${DEFAULT_LOCALE}.json`)).default as AbstractIntlMessages;
  }
}
