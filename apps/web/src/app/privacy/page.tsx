import Link from "next/link";
import { SiteHeader } from "@/components/marketing/site-header";

export const metadata = { title: "Chính sách bảo mật — VietVid" };

export default function PrivacyPage() {
  return (
    <main className="mesh-bg min-h-dvh">
      <SiteHeader />
      <article className="mx-auto max-w-3xl px-4 pb-24 pt-32 text-ink-medium">
        <h1 className="text-3xl font-bold text-ink-high">Chính sách bảo mật</h1>
        <p className="mt-2 text-sm text-ink-low">Cập nhật: 27/06/2026</p>

        <Section title="1. Dữ liệu chúng tôi thu thập">
          Email, tên hiển thị, ảnh/sản phẩm bạn tải lên để tạo video, lịch sử giao dịch credit và dữ
          liệu sử dụng cơ bản. Mật khẩu được lưu dưới dạng băm (bcrypt), không lưu bản gốc.
        </Section>
        <Section title="2. Mục đích sử dụng">
          Để cung cấp dịch vụ tạo video, xử lý thanh toán, hỗ trợ khách hàng và cải thiện sản phẩm. Dữ
          liệu của mỗi workspace được cách ly riêng (Row-Level Security).
        </Section>
        <Section title="3. Chia sẻ với bên thứ ba">
          Chúng tôi dùng nhà cung cấp xử lý ảnh/giọng/video (AI providers) và cổng thanh toán để vận
          hành. Chỉ chia sẻ dữ liệu tối thiểu cần thiết, không bán dữ liệu cá nhân.
        </Section>
        <Section title="4. Quyền của bạn">
          Bạn có quyền truy cập, chỉnh sửa và yêu cầu xoá tài khoản cùng dữ liệu liên quan. Sổ cái giao
          dịch tài chính được giữ theo quy định kế toán/thuế.
        </Section>
        <Section title="5. Bảo mật">
          Mã hoá khi truyền (TLS), kiểm soát truy cập theo vai trò, và giới hạn tần suất để chống lạm
          dụng. Không hệ thống nào tuyệt đối an toàn, nhưng chúng tôi áp dụng chuẩn ngành.
        </Section>
        <Section title="6. Liên hệ">
          Yêu cầu về dữ liệu cá nhân:{" "}
          <a className="text-violet-300" href="mailto:privacy@vietvid.vn">privacy@vietvid.vn</a>.
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
