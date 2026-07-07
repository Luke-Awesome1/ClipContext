"use client";

import Link from "next/link";
import { motion } from "framer-motion";

export default function StudioNavbar() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-white/[0.06] bg-[#06080a]/80 backdrop-blur-xl backdrop-saturate-150">
      <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5 sm:px-8">
        <Link
          href="/"
          className="rounded-full px-2 py-1 text-lg font-semibold tracking-tight text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/70 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0C0F0F]"
        >
          Lumina{" "}
          <span className="bg-gradient-to-r from-sky-300 to-blue-500 bg-clip-text text-transparent">
            AI
          </span>
        </Link>

        <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
          <Link
            href="/"
            className="rounded-full border border-white/[0.08] bg-white/[0.04] px-3 py-2 text-sm font-medium text-neutral-300 transition-all duration-300 hover:border-blue-400/20 hover:bg-blue-500/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/70 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0C0F0F]"
          >
            Back to home
          </Link>
        </motion.div>
      </nav>
    </header>
  );
}
