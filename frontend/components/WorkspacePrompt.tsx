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
      className="rounded-[1.6rem] border border-white/[0.08] bg-white/[0.03] p-6 shadow-[0_24px_90px_rgba(0,0,0,0.22)] backdrop-blur-xl"
    >
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-blue-400/20 bg-blue-500/10 text-blue-400">
          <Sparkles size={18} />
        </div>
        <div>
          <p className="text-sm font-semibold text-white">Save this project forever</p>
          <p className="text-sm text-neutral-400">Keep your work in a polished creator workspace.</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={continueWithoutWorkspace}
          className="rounded-full border border-white/[0.1] bg-white/[0.04] px-4 py-2.5 text-sm font-semibold text-white transition-all duration-200 hover:-translate-y-0.5 hover:border-white/20 hover:bg-white/[0.07] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/70 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0C0F0F]"
        >
          Continue without Workspace
        </button>
        <button
          type="button"
          onClick={createFreeWorkspace}
          className="inline-flex items-center gap-2 rounded-full bg-blue-500 px-4 py-2.5 text-sm font-semibold text-white shadow-[0_0_32px_rgba(91,140,255,0.24)] transition-all duration-200 hover:-translate-y-0.5 hover:bg-blue-400 hover:shadow-[0_0_42px_rgba(91,140,255,0.32)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/70 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0C0F0F]"
        >
          Create Free Workspace
          <ArrowRight size={16} />
        </button>
      </div>
    </motion.div>
  );
}
