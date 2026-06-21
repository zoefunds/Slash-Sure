"use client";

import { createContext, useContext, useState } from "react";

interface SidebarCtx {
  mobileOpen: boolean;
  openMobile: () => void;
  closeMobile: () => void;
}

const Ctx = createContext<SidebarCtx>({
  mobileOpen: false,
  openMobile: () => {},
  closeMobile: () => {},
});

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  return (
    <Ctx.Provider value={{ mobileOpen, openMobile: () => setMobileOpen(true), closeMobile: () => setMobileOpen(false) }}>
      {children}
    </Ctx.Provider>
  );
}

export const useSidebarCtx = () => useContext(Ctx);
