"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

interface AuthPromptModalProps {
  open: boolean;
  title: string;
  description: string;
  onClose: () => void;
  onSuccess?: () => void;
  dismissLabel?: string;
}

export default function AuthPromptModal({
  open,
  title,
  description,
  onClose,
  onSuccess,
  dismissLabel = "Not now",
}: AuthPromptModalProps) {
  const { loginWithGoogle, firebaseConfigured } = useAuth();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  // Portal this into document.body rather than rendering it in place: both
  // Navbar and StudioNavbar's <header> use backdrop-blur, which (per the
  // CSS spec) makes that header a new containing block for any
  // position:fixed descendant — so without the portal, this modal's
  // "fixed inset-0" centers inside the 64px-tall header instead of the
  // viewport. document.body isn't available during SSR, hence the mount
  // check.
  useEffect(() => {
    setMounted(true);
  }, []);

  const handleContinue = async () => {
    setPending(true);
    setError(null);

    try {
      await loginWithGoogle();
      onSuccess?.();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed. Please try again.");
    } finally {
      setPending(false);
    }
  };

  if (!mounted) return null;

  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-neutral-950/40 px-4 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, y: 12, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
            transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-sm rounded-lg border border-neutral-200 bg-white p-6 shadow-xl"
          >
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <p className="text-base font-semibold text-neutral-950">{title}</p>
                <p className="mt-1 text-sm text-neutral-600">{description}</p>
              </div>
              <button
                type="button"
                onClick={onClose}
                aria-label="Close"
                className="shrink-0 rounded-full p-1 text-neutral-400 transition-colors hover:bg-neutral-100 hover:text-neutral-700"
              >
                <X size={18} />
              </button>
            </div>

            {!firebaseConfigured && (
              <p className="mb-3 text-sm text-amber-600">
                Sign-in isn&apos;t configured on this server yet.
              </p>
            )}

            {error && <p className="mb-3 text-sm text-red-600">{error}</p>}

            <div className="flex flex-col gap-2">
              <button
                type="button"
                onClick={handleContinue}
                disabled={pending || !firebaseConfigured}
                className="inline-flex items-center justify-center gap-2 rounded-full bg-neutral-950 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:bg-[#365f53] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {pending ? "Connecting…" : "Continue with Google"}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="rounded-full border border-neutral-300 bg-white px-4 py-2.5 text-sm font-semibold text-neutral-700 transition-colors hover:border-neutral-400"
              >
                {dismissLabel}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body,
  );
}
