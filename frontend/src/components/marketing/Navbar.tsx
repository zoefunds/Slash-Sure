"use client";

import Link from "next/link";
import { useState } from "react";
import { Menu, X } from "lucide-react";
import { LogoIcon } from "@/components/ui/Logo";

const navLinks = [
  { href: "/#features", label: "Features" },
  { href: "/#networks", label: "Networks" },
  { href: "/#how-it-works", label: "How It Works" },
];

export function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-border bg-background/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-6 h-15 flex items-center justify-between" style={{ height: "60px" }}>
        <Link href="/" className="flex items-center gap-2.5 font-bold text-lg tracking-tight">
          <LogoIcon className="w-7 h-7" />
          <span className="text-foreground">SlashSure</span>
        </Link>

        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              {l.label}
            </Link>
          ))}
        </nav>

        <div className="hidden md:flex items-center gap-3">
          <Link
            href="/login"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors px-4 py-2"
          >
            Sign In
          </Link>
          <Link
            href="/register"
            className="text-sm bg-foreground text-background hover:opacity-85 px-4 py-2 rounded-lg transition-opacity font-medium"
          >
            Get Started
          </Link>
        </div>

        <button className="md:hidden text-foreground" onClick={() => setOpen(!open)}>
          {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t border-border bg-background px-6 py-4 space-y-3">
          {navLinks.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="block text-sm text-muted-foreground hover:text-foreground py-2"
              onClick={() => setOpen(false)}
            >
              {l.label}
            </Link>
          ))}
          <div className="pt-2 flex flex-col gap-2">
            <Link href="/login" className="text-sm py-2 text-center border border-border rounded-lg">Sign In</Link>
            <Link href="/register" className="text-sm bg-foreground text-background px-4 py-2 rounded-lg text-center font-medium">
              Get Started
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
