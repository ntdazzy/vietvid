import Link from "next/link";
import { SiteHeader } from "@/components/marketing/site-header";

export const metadata = { title: "Điều khoản sử dụng — Vyra" };

export default function TermsPage() {
  return (
    <main className="mesh-bg min-h-dvh">
      <SiteHeader />
      <article className="mx-auto max-w-3xl px-4 pb-24 pt-32 text-ink-medium">
        <h1 className="text-3xl font-bold text-ink-high">Điều khoản sử dụng</h1>
        <p className="mt-2 text-sm text-ink-low">Cập nhật: 27/06/2026</p>

        <Section title="1. Chấp nhận điều khoản">
          Khi tạo tài khoản và sử dụng Vyra, bạn đồng ý với các điều khoản này. Nếu không đồng ý,
          vui lòng ngừng sử dụng dịch vụ.
        </Section>
        <Section title="2. Dịch vụ">
          Vyra cung cấp công cụ tạo video marketing bằng AI với giọng đọc tiếng Việt. Dịch vụ vận
          hành theo mô hình credit: bạn nạp credit và tiêu khi tạo video. Chúng tôi hoàn 100% credit
          nếu lỗi phát sinh từ hệ thống.
        </Section>
        <Section title="3. Nội dung & quyền hình ảnh (KOL AI)">
          Bạn chịu trách nhiệm về nội dung, sản phẩm và hình ảnh bạn tải lên. Khi dùng tính năng tạo
          người mẫu/giọng AI, bạn cam kết có quyền hợp pháp với hình ảnh, giọng nói gốc và đồng ý cho
          phép xử lý. Cấm tạo nội dung mạo danh, lừa đảo, vi phạm pháp luật Việt Nam hoặc chính sách
          nền tảng (TikTok/YouTube/Facebook).
        </Section>
        <Section title="4. Thanh toán & credit">
          Giá và số credit hiển thị tại trang Bảng giá. Credit đã tiêu cho video hoàn tất không được
          hoàn, trừ lỗi hệ thống. Mọi giao dịch được ghi vào sổ cái minh bạch trong tài khoản.
        </Section>
        <Section title="5. Giới hạn trách nhiệm">
          Dịch vụ cung cấp "nguyên trạng". Vyra không chịu trách nhiệm cho thiệt hại gián tiếp phát
          sinh từ việc sử dụng video được tạo ra.
        </Section>
        <Section title="6. Liên hệ">
          Mọi thắc mắc: <a className="text-violet-300" href="mailto:support@vietvid.vn">support@vietvid.vn</a>.
        </Section>

        <Link href="/" className="mt-10 inline-block text-sm text-violet-300 hover:text-violet-200">
          ← Về trang chủ
        </Link>
      </article>
    </main>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-8">
      <h2 className="text-lg font-semibold text-ink-high">{title}</h2>
      <p className="mt-2 leading-relaxed">{children}</p>
    </section>
  );
}
