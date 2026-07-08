"use client";

import { motion } from "framer-motion";
import { ArrowRight, CheckCircle2, PlugZap, Sparkles } from "lucide-react";

const platforms = [
  { name: "YouTube", status: "Connected", tone: "text-red-400" },
  { name: "Instagram", status: "Connected", tone: "text-pink-400" },
  { name: "TikTok", status: "Ready", tone: "text-[#365f53]" },
  { name: "LinkedIn", status: "Pending", tone: "text-slate-400" },
];

export default function ConnectedPlatformsPanel() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      className="rounded-lg border border-neutral-200 bg-white/70 p-6 shadow-sm backdrop-blur-xl"
    >
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-neutral-950">Connected platforms</p>
          <p className="text-sm text-neutral-600">Ready for publishing and OAuth hooks.</p>
        </div>
        <div className="rounded-full border border-[#365f53]/20 bg-[#365f53]/10 p-2 text-[#365f53]">
          <PlugZap size={16} />
        </div>
      </div>

      <div className="space-y-3">
        {platforms.map((platform, index) => (
          <motion.div
            key={platform.name}
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.05 * index }}
            className="flex items-center justify-between rounded-lg border border-neutral-200 bg-[#faf9f6] px-3 py-3"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full border border-neutral-200 bg-white text-sm font-semibold text-neutral-700">
                {platform.name.charAt(0)}
              </div>
              <div>
                <p className="text-sm font-medium text-neutral-950">{platform.name}</p>
                <p className="text-xs text-neutral-500">{platform.status}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-xs font-medium ${platform.tone}`}>{platform.status}</span>
              {platform.status === "Connected" ? (
                <CheckCircle2 size={15} className="text-emerald-400" />
              ) : (
                <Sparkles size={15} className="text-[#365f53]" />
              )}
            </div>
          </motion.div>
        ))}
      </div>

      <button
        type="button"
        className="mt-5 inline-flex items-center gap-2 rounded-full border border-neutral-300 bg-white px-4 py-2.5 text-sm font-semibold text-neutral-900 transition-all duration-200 hover:-translate-y-0.5 hover:border-[#365f53]/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
      >
        Connect more platforms
        <ArrowRight size={16} />
      </button>
    </motion.div>
  );
}
