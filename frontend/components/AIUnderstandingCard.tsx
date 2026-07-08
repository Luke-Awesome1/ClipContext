"use client";

import { motion } from "framer-motion";
import { Brain, Eye, MessageSquare, Sparkles } from "lucide-react";
import type { VideoContextSummary } from "@/types/video";

interface AIUnderstandingCardProps {
  videoContext: VideoContextSummary;
}

const FIELDS = [
  { key: "topic", label: "Topic", icon: MessageSquare },
  { key: "content_type", label: "Content Type", icon: Eye },
  { key: "core_message", label: "Core Message", icon: Sparkles },
  { key: "multimodal_summary", label: "Multimodal Summary", icon: Brain },
] as const;

export default function AIUnderstandingCard({ videoContext }: AIUnderstandingCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="rounded-lg border border-neutral-200 bg-white/70 p-6 shadow-sm backdrop-blur-xl"
    >
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#365f53]/20 bg-[#365f53]/10 text-[#365f53]">
          <Brain size={20} strokeWidth={1.75} />
        </div>
        <div>
          <h3 className="text-base font-semibold text-neutral-950">VideoContext Signals</h3>
          <p className="text-xs text-neutral-500">
            Speech and visual evidence used for generation
          </p>
        </div>
      </div>

      <ul className="space-y-3">
        {FIELDS.map((field, i) => {
          const Icon = field.icon;
          const value = videoContext[field.key];

          return (
            <motion.li
              key={field.key}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.35, delay: 0.05 * i }}
              className="flex items-start gap-3 rounded-lg border border-neutral-200 bg-[#faf9f6] px-3 py-3"
            >
              <Icon size={16} className="mt-0.5 shrink-0 text-[#365f53]" />
              <div className="min-w-0 flex-1">
                <p className="text-[10px] uppercase tracking-wider text-neutral-600">
                  {field.label}
                </p>
                <p className="mt-1 text-sm leading-snug text-neutral-800">{value}</p>
              </div>
            </motion.li>
          );
        })}
      </ul>
    </motion.div>
  );
}
