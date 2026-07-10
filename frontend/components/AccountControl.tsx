"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { FolderOpen, LogOut } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import AuthPromptModal from "@/components/AuthPromptModal";

// ClipContext account control — reflects Firebase auth state only. This is
// deliberately separate from YouTube connection state (see
// YouTubeUploadPanel): a user can be logged into ClipContext without ever
// connecting YouTube, and vice versa.
export default function AccountControl() {
  const { user, loading, isAuthenticated, logout } = useAuth();
  const [authIntent, setAuthIntent] = useState<"login" | "signup" | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // A "fixed inset-0" click-catcher would be trapped inside the header's
  // own box when the header has backdrop-blur applied (see
  // AuthPromptModal.tsx for the full explanation) — a document-level
  // listener sidesteps that entirely.
  useEffect(() => {
    if (!menuOpen) return;

    const onPointerDown = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, [menuOpen]);

  if (loading) return null;

  if (!isAuthenticated) {
    return (
      <>
        <div className="hidden items-center gap-5 md:flex">
          <button
            type="button"
            onClick={() => setAuthIntent("login")}
            className="text-sm font-medium text-neutral-600 transition-colors duration-300 hover:text-neutral-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
          >
            Log In
          </button>
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <button
              type="button"
              onClick={() => setAuthIntent("signup")}
              className="inline-flex items-center rounded-full bg-neutral-950 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-all duration-300 hover:bg-[#365f53] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
            >
              Get Started
            </button>
          </motion.div>
        </div>

        <AuthPromptModal
          open={authIntent !== null}
          title={authIntent === "signup" ? "Create your ClipContext account" : "Log in to ClipContext"}
          description="Use Google to continue — this also creates your account on first sign-in."
          onClose={() => setAuthIntent(null)}
        />
      </>
    );
  }

  const initials = (user?.displayName ?? user?.email ?? "U").charAt(0).toUpperCase();

  return (
    <div ref={menuRef} className="relative hidden md:block">
      <button
        type="button"
        onClick={() => setMenuOpen((v) => !v)}
        aria-expanded={menuOpen}
        className="flex items-center gap-2 rounded-full border border-neutral-200 bg-white/70 py-1.5 pl-1.5 pr-3 transition-colors hover:border-[#365f53]/25 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
      >
        {user?.photoURL ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={user.photoURL} alt="" className="h-7 w-7 rounded-full object-cover" />
        ) : (
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[#365f53]/10 text-xs font-semibold text-[#365f53]">
            {initials}
          </span>
        )}
        <span className="max-w-[8rem] truncate text-sm font-medium text-neutral-800">
          {user?.displayName ?? user?.email ?? "Account"}
        </span>
      </button>

      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.18 }}
            className="absolute right-0 z-50 mt-2 w-48 overflow-hidden rounded-lg border border-neutral-200 bg-white shadow-lg"
          >
            <Link
              href="/artifacts"
              onClick={() => setMenuOpen(false)}
              className="flex items-center gap-2 px-4 py-2.5 text-sm text-neutral-700 transition-colors hover:bg-neutral-50"
            >
              <FolderOpen size={14} />
              My Artifacts
            </Link>
            <button
              type="button"
              onClick={() => {
                setMenuOpen(false);
                logout();
              }}
              className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm text-neutral-700 transition-colors hover:bg-neutral-50"
            >
              <LogOut size={14} />
              Log Out
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
