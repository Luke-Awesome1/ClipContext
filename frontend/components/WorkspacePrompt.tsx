"use client";

import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { useVideoSession } from "@/context/VideoSessionContext";

export default function WorkspacePrompt() {
  const { continueWithoutWorkspace, createFreeWorkspace } = useVideoSession();

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      className="rounded-lg border border-neutral-200 bg-white/70 p-6 shadow-sm backdrop-blur-xl"
    >
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#365f53]/20 bg-[#365f53]/10 text-[#365f53]">
          <Sparkles size={18} />
        </div>
        <div>
          <p className="text-sm font-semibold text-neutral-950">Save this project</p>
          <p className="text-sm text-neutral-600">Keep generated artifacts in a creator workspace.</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={continueWithoutWorkspace}
          className="rounded-full border border-neutral-300 bg-white px-4 py-2.5 text-sm font-semibold text-neutral-900 transition-all duration-200 hover:-translate-y-0.5 hover:border-[#365f53]/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
        >
          Continue without Workspace
        </button>
        <button
          type="button"
          onClick={createFreeWorkspace}
          className="inline-flex items-center gap-2 rounded-full bg-neutral-950 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#365f53] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
        >
          Create Free Workspace
          <ArrowRight size={16} />
        </button>
      </div>
    </motion.div>
  );
}
