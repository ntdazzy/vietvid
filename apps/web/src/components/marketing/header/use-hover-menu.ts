"use client";

import { useRef, useState } from "react";

export type MenuKey = "tools" | "models" | "features" | "resources";

export function useHoverMenu() {
  const [open, setOpen] = useState<null | MenuKey>(null);

  // Fix "di vào menu là mất": đóng có ĐỘ TRỄ; rê qua khe trigger→panel không bị đóng.
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cancelClose = () => {
    if (closeTimer.current) clearTimeout(closeTimer.current);
  };
  const openMenu = (k: MenuKey | null) => {
    cancelClose();
    setOpen(k);
  };
  const scheduleClose = () => {
    cancelClose();
    closeTimer.current = setTimeout(() => setOpen(null), 180);
  };

  return { open, openMenu, scheduleClose, cancelClose };
}
