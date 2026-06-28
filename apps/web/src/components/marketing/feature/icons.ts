// string → lucide icon, để feature-pages.ts giữ là file dữ liệu thuần (tham chiếu icon bằng tên).
import {
  Sparkles, Mic, UserCheck, Captions, Shirt, Images, Crop, Zap, Coins, GitBranch,
  Link2, Type, Image, Layers, Wand2, Timer, Download, Play, AudioLines, Film,
  Volume2, BarChart3, ArrowRight, Megaphone, Palette, ShoppingBag, Repeat, type LucideIcon,
} from "lucide-react";

export const ICONS: Record<string, LucideIcon> = {
  Sparkles, Mic, UserCheck, Captions, Shirt, Images, Crop, Zap, Coins, GitBranch,
  Link2, Type, Image, Layers, Wand2, Timer, Download, Play, AudioLines, Film,
  Volume2, BarChart3, ArrowRight, Megaphone, Palette, ShoppingBag, Repeat,
};

export function icon(name?: string): LucideIcon {
  return (name && ICONS[name]) || Sparkles;
}
