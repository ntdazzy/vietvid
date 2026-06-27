import type { Config } from "tailwindcss";
import animate from "tailwindcss-animate";

// Token CHUẨN theo docs/WEB-DESIGN-PLAN.md §0.3 + §B (Dark Cinematic × Violet→Blue).
const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: { base: "#06070D", surface: "#0B0D16", surface2: "#12141F", elevated: "#1A1C2A" },
        violet: {
          50: "#F2EEFF", 100: "#E4DBFF", 200: "#C9B6FF", 300: "#A98CFF", 400: "#8B5CFF",
          500: "#7C4DFF", 600: "#6A3CF0", 700: "#5A2FD6", 800: "#4322A8", 900: "#2E1772",
        },
        indigo: { 500: "#6366F1" },
        brandblue: { 400: "#4C8DFF", 500: "#3B82F6", 600: "#2D6BE0" },
        ink: { high: "#F4F5FA", medium: "#B4B7C7", low: "#7E8298", disabled: "#4B4E61" },
        success: "#34D399", hold: "#FBBF24", settle: "#B4B7C7",
        refund: "#22D3EE", danger: "#F87171", info: "#60A5FA",
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        sans: ["var(--font-body)", "system-ui", "sans-serif"],
        numeric: ["var(--font-numeric)", "var(--font-body)", "sans-serif"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: { lg: "12px", xl: "16px", "2xl": "20px", "3xl": "28px" },
      boxShadow: {
        "glow-sm": "0 0 16px rgba(124,77,255,.35)",
        "glow-md": "0 0 32px rgba(124,77,255,.45)",
        "glow-lg": "0 0 64px rgba(124,77,255,.40)",
        "glow-blue": "0 0 40px rgba(59,130,246,.40)",
        "glow-success": "0 0 28px rgba(52,211,153,.40)",
        "inset-hl": "inset 0 1px 0 rgba(255,255,255,.06)",
      },
      backgroundImage: {
        "grad-brand": "linear-gradient(135deg,#7C4DFF 0%,#6366F1 50%,#3B82F6 100%)",
        "grad-brand-soft": "linear-gradient(135deg,rgba(124,77,255,.18),rgba(59,130,246,.18))",
        "glow-radial":
          "radial-gradient(60% 60% at 50% 0%, rgba(124,77,255,.30) 0%, rgba(99,102,241,.10) 40%, transparent 72%)",
      },
      keyframes: {
        shimmer: { "100%": { transform: "translateX(100%)" } },
        "glow-pulse": { "0%,100%": { opacity: "0.55" }, "50%": { opacity: "1" } },
        float: { "0%,100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-8px)" } },
        aurora: {
          "0%,100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        shimmer: "shimmer 1.8s infinite",
        "glow-pulse": "glow-pulse 2.4s ease-in-out infinite",
        float: "float 6s ease-in-out infinite",
        aurora: "aurora 16s ease infinite",
        "fade-up": "fade-up .6s cubic-bezier(.22,1,.36,1) both",
      },
    },
  },
  plugins: [animate],
};

export default config;
