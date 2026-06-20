import Link from "next/link";

const links = {
  Product: [
    { label: "Features", href: "/#features" },
    { label: "How It Works", href: "/#how-it-works" },
    { label: "Networks", href: "/#networks" },
    { label: "Dashboard", href: "/login" },
  ],
  Company: [
    { label: "Get Started", href: "/register" },
    { label: "Sign In", href: "/login" },
    { label: "GenLayer", href: "https://genlayer.com" },
  ],
  Networks: [
    { label: "EigenLayer", href: "#" },
    { label: "Symbiotic", href: "#" },
    { label: "Babylon", href: "#" },
    { label: "Cosmos", href: "#" },
  ],
};

export function Footer() {
  return (
    <footer className="border-t border-border px-6 py-16 bg-card">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
          <div>
            <Link href="/" className="flex items-center gap-2 font-bold text-base mb-4">
              <div className="w-6 h-6 bg-foreground rounded flex items-center justify-center">
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                  <path d="M5 0.5L9.5 3V7L5 9.5L0.5 7V3L5 0.5Z" fill="#efece4" />
                </svg>
              </div>
              <span>SlashSure</span>
            </Link>
            <p className="text-sm text-muted-foreground leading-relaxed">
              The AI-powered trust, slashing, and insurance layer for decentralized networks.
              Powered by GenLayer.
            </p>
          </div>

          {Object.entries(links).map(([category, items]) => (
            <div key={category}>
              <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-4">{category}</h3>
              <ul className="space-y-2.5">
                {items.map((item) => (
                  <li key={item.label}>
                    <Link
                      href={item.href}
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="pt-8 border-t border-border flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} SlashSure. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            <Link href="#" className="text-xs text-muted-foreground hover:text-foreground transition-colors">Privacy</Link>
            <Link href="#" className="text-xs text-muted-foreground hover:text-foreground transition-colors">Terms</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
