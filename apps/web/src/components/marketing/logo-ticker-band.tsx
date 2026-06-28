// Dải chữ chạy ngang (nhịp nghỉ giữa các act) — các sàn/định dạng/năng lực Vyra phục vụ.
const ITEMS = [
  "Shopee", "TikTok Shop", "Lazada", "Reels", "Shorts", "API B2B", "Webhook",
  "9:16", "1:1", "16:9", "7 giọng Việt", "Phụ đề khớp khung", "Đo click",
];

const MASK = {
  maskImage: "linear-gradient(to right, transparent, #000 6%, #000 94%, transparent)",
  WebkitMaskImage: "linear-gradient(to right, transparent, #000 6%, #000 94%, transparent)",
} as const;

export function LogoTickerBand() {
  const track = [...ITEMS, ...ITEMS, ...ITEMS, ...ITEMS]; // đủ rộng để loop liền
  return (
    <div className="relative left-1/2 right-1/2 -mx-[50vw] w-screen overflow-hidden border-y border-white/[0.05] py-6" style={MASK}>
      <div className="flex w-max animate-marquee items-center hover:[animation-play-state:paused]" style={{ animationDuration: "55s" }}>
        {track.map((t, i) => (
          <span key={i} className="flex items-center whitespace-nowrap text-sm font-medium text-ink-low">
            {t}
            <span className="mx-5 h-1 w-1 rounded-full bg-violet-400/70" />
          </span>
        ))}
      </div>
    </div>
  );
}
