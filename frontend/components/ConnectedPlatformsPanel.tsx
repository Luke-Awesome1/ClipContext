"use client";

import { motion } from "framer-motion";
import { ArrowRight, CheckCircle2, PlugZap, Sparkles } from "lucide-react";

const platforms = [
  { name: "YouTube", status: "Connected", tone: "text-red-400" },
  { name: "Instagram", status: "Connected", tone: "text-pink-400" },
  { name: "TikTok", status: "Ready", tone: "text-sky-400" },
  { name: "LinkedIn", status: "Pending", tone: "text-slate-400" },
];

export default function ConnectedPlatformsPanel() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      className="rounded-[1.6rem] border border-white/[0.08] bg-white/[0.03] p-6 shadow-[0_24px_90px_rgba(0,0,0,0.22)] backdrop-blur-xl"
    >
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-white">Connected platforms</p>
          <p className="text-sm text-neutral-400">A polished frontend shell ready for OAuth hooks.</p>
        </div>
        <div className="rounded-full border border-blue-400/20 bg-blue-500/10 p-2 text-blue-400">
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
            className="flex items-center justify-between rounded-2xl border border-white/[0.06] bg-black/20 px-3 py-3"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full border border-white/[0.08] bg-white/[0.05] text-sm font-semibold text-white">
                {platform.name.charAt(0)}
              </div>
              <div>
                <p className="text-sm font-medium text-white">{platform.name}</p>
                <p className="text-xs text-neutral-500">{platform.status}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-xs font-medium ${platform.tone}`}>{platform.status}</span>
              {platform.status === "Connected" ? (
                <CheckCircle2 size={15} className="text-emerald-400" />
              ) : (
                <Sparkles size={15} className="text-blue-400" />
              )}
            </div>
          </motion.div>
        ))}
      </div>

      <button
        type="button"
        className="mt-5 inline-flex items-center gap-2 rounded-full border border-white/[0.1] bg-white/[0.04] px-4 py-2.5 text-sm font-semibold text-white transition-all duration-200 hover:-translate-y-0.5 hover:border-blue-400/30 hover:bg-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/70 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0C0F0F]"
      >
        Connect more platforms
        <ArrowRight size={16} />
      </button>
    </motion.div>
  );
}
