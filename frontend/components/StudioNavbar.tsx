"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import AccountControl from "@/components/AccountControl";

export default function StudioNavbar() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-neutral-200 bg-[#f6f5f2]/85 backdrop-blur-xl backdrop-saturate-150">
      <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-5 sm:px-8">
        <Link
          href="/"
          className="rounded-full px-2 py-1 text-lg font-semibold tracking-tight text-neutral-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
        >
          Clip<span className="text-[#365f53]">Context</span>
        </Link>

        <div className="flex items-center gap-3">
          <AccountControl />

          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Link
              href="/"
              className="rounded-full border border-neutral-300 bg-white/65 px-3 py-2 text-sm font-medium text-neutral-700 transition-all duration-300 hover:border-[#365f53]/25 hover:bg-white hover:text-neutral-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
            >
              Back to home
            </Link>
          </motion.div>
        </div>
      </nav>
    </header>
  );
}
