import { getRequestConfig } from "next-intl/server";
import { getLocale, getMessages } from "./server";

// Cấu hình request cho next-intl ở server (RSC) — bật API getTranslations().
// Không-routing: locale lấy từ cookie (getLocale), messages load theo locale.
export default getRequestConfig(async () => {
  const locale = getLocale();
  return { locale, messages: await getMessages(locale) };
});
