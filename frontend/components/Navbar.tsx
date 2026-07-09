"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FolderOpen, LogOut, Menu, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/context/AuthContext";
import AccountControl from "@/components/AccountControl";
import AuthPromptModal from "@/components/AuthPromptModal";

const navLinks = [
  { label: "Upload", href: "#upload" },
  { label: "Features", href: "#features" },
  { label: "Pipeline", href: "#pipeline" },
  { label: "Technology", href: "#technology" },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const [mobileAuthIntent, setMobileAuthIntent] = useState<"login" | "signup" | null>(null);
  const { isAuthenticated, loading, logout } = useAuth();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled
          ? "border-b border-neutral-200 bg-[#f6f5f2]/85 backdrop-blur-xl backdrop-saturate-150"
          : "bg-transparent"
      }`}
    >
      <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5 sm:px-8">
        <Link
          href="/"
          className="group flex items-center gap-2 rounded-full px-2 py-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
        >
          <span className="text-lg font-semibold tracking-tight text-neutral-950">
            ClipContext{" "}
            <span className="text-[#365f53]">
              AI
            </span>
          </span>
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          {navLinks.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className="group relative rounded-full px-2 py-1 text-sm font-medium text-neutral-600 transition-all duration-300 hover:text-neutral-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
            >
              {item.label}
              <span className="absolute inset-x-0 -bottom-1 h-px scale-x-0 rounded-full bg-[#365f53] transition-transform duration-300 group-hover:scale-x-100" />
            </Link>
          ))}
        </div>

        <AccountControl />

        <button
          type="button"
          aria-label="Toggle menu"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
          className="rounded-lg p-2 text-neutral-700 transition hover:bg-neutral-200/60 hover:text-neutral-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2] md:hidden"
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </nav>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="border-b border-neutral-200 bg-[#f6f5f2]/95 backdrop-blur-xl md:hidden"
          >
            <div className="mx-auto flex max-w-6xl flex-col gap-1 px-5 py-4">
              {navLinks.map((item) => (
                <Link
                  key={item.label}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className="rounded-lg px-3 py-3 text-base font-medium text-neutral-800 transition hover:bg-neutral-200/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
                >
                  {item.label}
                </Link>
              ))}

              {!loading && (
                <div className="mt-4 flex flex-col gap-1 border-t border-neutral-200 pt-4">
                  {isAuthenticated ? (
                    <>
                      <Link
                        href="/artifacts"
                        onClick={() => setOpen(false)}
                        className="flex items-center gap-2 rounded-lg px-3 py-3 text-base font-medium text-neutral-800 transition hover:bg-neutral-200/60"
                      >
                        <FolderOpen size={16} />
                        My Artifacts
                      </Link>
                      <button
                        type="button"
                        onClick={() => {
                          setOpen(false);
                          logout();
                        }}
                        className="flex items-center gap-2 rounded-lg px-3 py-3 text-left text-base font-medium text-neutral-800 transition hover:bg-neutral-200/60"
                      >
                        <LogOut size={16} />
                        Log Out
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        type="button"
                        onClick={() => setMobileAuthIntent("login")}
                        className="rounded-lg px-3 py-3 text-center text-neutral-700 transition hover:bg-neutral-200/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
                      >
                        Log In
                      </button>
                      <button
                        type="button"
                        onClick={() => setMobileAuthIntent("signup")}
                        className="rounded-full bg-neutral-950 py-3 text-center text-sm font-semibold text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
                      >
                        Get Started
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AuthPromptModal
        open={mobileAuthIntent !== null}
        title={
          mobileAuthIntent === "signup" ? "Create your ClipContext account" : "Log in to ClipContext"
        }
        description="Use Google to continue — this also creates your account on first sign-in."
        onClose={() => setMobileAuthIntent(null)}
        onSuccess={() => setOpen(false)}
      />
    </header>
  );
}
