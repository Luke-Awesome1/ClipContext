"use client";

import { motion } from "framer-motion";
import { Brain, Eye, MessageSquare } from "lucide-react";
import type { DetectedConcept } from "@/types/video";

const categoryMeta = {
  speech: { icon: MessageSquare, label: "Speech", color: "text-sky-400" },
  visual: { icon: Eye, label: "Visual", color: "text-violet-400" },
  context: { icon: Brain, label: "Context", color: "text-blue-400" },
} as const;

interface AIUnderstandingCardProps {
  concepts: DetectedConcept[];
}

export default function AIUnderstandingCard({ concepts }: AIUnderstandingCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6 backdrop-blur-xl"
    >
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/[0.08] bg-blue-500/10 text-blue-400">
          <Brain size={20} strokeWidth={1.75} />
        </div>
        <div>
          <h3 className="text-base font-semibold text-white">AI Understanding</h3>
          <p className="text-xs text-neutral-500">
            Multimodal signals detected in your video
          </p>
        </div>
      </div>

      <ul className="space-y-3">
        {concepts.map((concept, i) => {
          const meta = categoryMeta[concept.category];
          const Icon = meta.icon;
          return (
            <motion.li
              key={concept.label}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.35, delay: 0.05 * i }}
              className="flex items-start gap-3 rounded-xl border border-white/[0.05] bg-black/20 px-3 py-3"
            >
              <Icon size={16} className={`mt-0.5 shrink-0 ${meta.color}`} />
              <div className="min-w-0 flex-1">
                <p className="text-sm leading-snug text-neutral-200">
                  {concept.label}
                </p>
                <p className="mt-1 text-[10px] uppercase tracking-wider text-neutral-600">
                  {meta.label}
                </p>
              </div>
              <span className="shrink-0 rounded-md bg-white/[0.05] px-2 py-0.5 text-xs font-medium text-neutral-400">
                {concept.confidence}%
              </span>
            </motion.li>
          );
        })}
      </ul>
    </motion.div>
  );
}
