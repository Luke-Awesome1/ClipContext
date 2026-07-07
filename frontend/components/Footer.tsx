import Link from "next/link";
import SectionReveal from "@/components/ui/SectionReveal";

const footerLinks = {
  Product: [
    { label: "Features", href: "#features" },
    { label: "Technology", href: "#technology" },
    { label: "Demo", href: "#upload" },
  ],
  Company: [
    { label: "About", href: "#" },
    { label: "Blog", href: "#" },
    { label: "Careers", href: "#" },
  ],
  Legal: [
    { label: "Privacy", href: "#" },
    { label: "Terms", href: "#" },
  ],
};

export default function Footer() {
  return (
    <footer className="border-t border-white/[0.06] bg-[#0C0F0F]">
      <div className="mx-auto max-w-6xl px-5 py-16 sm:px-8">
        <SectionReveal delay={0.04} className="grid gap-12 sm:grid-cols-2 lg:grid-cols-4">
          <div className="lg:col-span-1">
            <Link href="/" className="text-lg font-semibold text-white">
              Lumina{" "}
              <span className="bg-gradient-to-r from-sky-300 to-blue-500 bg-clip-text text-transparent">
                AI
              </span>
            </Link>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-neutral-500">
              Multimodal intelligence for video creators. Understand every
              frame. Publish with confidence.
            </p>
          </div>

          {Object.entries(footerLinks).map(([group, links]) => (
            <div key={group}>
              <h4 className="mb-4 text-xs font-semibold uppercase tracking-wider text-neutral-400">
                {group}
              </h4>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-sm text-neutral-500 transition-colors duration-300 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/70 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0C0F0F]"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </SectionReveal>

        <div className="mt-16 flex flex-col items-center justify-between gap-4 border-t border-white/[0.06] pt-8 sm:flex-row">
          <p className="text-xs text-neutral-600">
            © {new Date().getFullYear()} Lumina AI. All rights reserved.
          </p>
          <p className="text-xs text-neutral-600">
            Built for creators who refuse to compromise on quality.
          </p>
        </div>
      </div>
    </footer>
  );
}
