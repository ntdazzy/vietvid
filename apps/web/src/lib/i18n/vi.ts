// Copy tiếng Việt tập trung (mục §8.5 plan). Copy cụ-thể-số-Việt, KHÔNG sáo rỗng.
export const vi = {
  brand: "VietVid",
  tagline: "Tạo video bán hàng, giọng Việt thật.",
  nav: {
    product: "Sản phẩm",
    pricing: "Bảng giá",
    demo: "Nghe thử",
    login: "Đăng nhập",
    create: "Tạo video",
    dashboard: "Bảng điều khiển",
    library: "Thư viện",
    billing: "Ví & Nạp",
    settings: "Cài đặt",
  },
  hero: {
    eyebrow: "VIDEO AI · GIỌNG VIỆT THẬT",
    title_1: "1 ảnh sản phẩm →",
    title_2: "video chốt đơn 60 giây.",
    sub: "Giọng Việt thật (không phải robot). Thấy trước tốn bao nhiêu credit rồi mới tạo. Hoàn 100% nếu lỗi hệ thống.",
    cta_primary: "Tạo video miễn phí",
    cta_voice: "Nghe thử giọng A/B",
  },
  credit: {
    balance: "Số dư",
    held: "Đang giữ",
    unit: "credit",
    estimate: "Ước tính",
    refundPromise: "Hoàn 100% nếu lỗi hệ thống",
  },
  wallet: {
    title: "Ví & Sổ cái",
    topup: "Nạp credit",
  },
  states: {
    loading: "Đang tải…",
    empty_jobs: "Chưa có video nào. Tạo video đầu tiên của bạn.",
    error: "Có lỗi xảy ra",
  },
  login: {
    title: "Đăng nhập VietVid",
    dev: "Đăng nhập nhanh (Dev)",
    devHint: "Chế độ dev: tạo phiên thử nghiệm + tặng credit free để trải nghiệm ngay.",
    google: "Tiếp tục với Google",
    email: "Tiếp tục với Email",
  },
} as const;

export type Dict = typeof vi;
