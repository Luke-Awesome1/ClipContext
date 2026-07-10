"use client";

import { motion } from "framer-motion";
import { Brain, Cpu, Eye, MessageSquare, Sparkles } from "lucide-react";
import type { StageAiAudit, VideoContextSummary } from "@/types/video";

interface AIUnderstandingCardProps {
  videoContext: VideoContextSummary;
  aiAudit?: StageAiAudit[];
}

const FIELDS = [
  { key: "topic", label: "Topic", icon: MessageSquare },
  { key: "content_type", label: "Content Type", icon: Eye },
  { key: "core_message", label: "Core Message", icon: Sparkles },
  { key: "multimodal_summary", label: "Multimodal Summary", icon: Brain },
] as const;

const STAGE_LABELS: Record<string, string> = {
  content_generation: "Content generation",
  discriminator: "Candidate ranking",
};

export default function AIUnderstandingCard({
  videoContext,
  aiAudit = [],
}: AIUnderstandingCardProps) {
  // Only ever surfaced when the orchestrator's audit says AMD actually
  // handled the stage — never for a stage that fell back to Fireworks.
  // See src/ai/providers/orchestrator.py.
  const amdStages = aiAudit.filter((entry) => entry.provider_used === "amd_vllm");
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

      {amdStages.length > 0 && (
        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-neutral-200 pt-4">
          {amdStages.map((entry) => (
            <span
              key={entry.stage}
              title={[entry.model, entry.hardware, entry.latency_ms ? `${Math.round(entry.latency_ms)}ms` : null]
                .filter(Boolean)
                .join(" · ")}
              className="inline-flex items-center gap-1.5 rounded-full border border-[#365f53]/20 bg-[#365f53]/5 px-2.5 py-1 text-[10px] font-medium uppercase tracking-wider text-[#365f53]"
            >
              <Cpu size={11} strokeWidth={2} />
              {STAGE_LABELS[entry.stage] ?? entry.stage}: AMD GPU inference
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
}
