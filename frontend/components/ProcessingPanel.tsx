"use client";

import { motion } from "framer-motion";
import { Check, Circle } from "lucide-react";
import { PIPELINE_STAGES } from "@/lib/generatedContent";
import type { PipelineStageId } from "@/types/video";
import SectionReveal from "@/components/ui/SectionReveal";

type StageStatus = "pending" | "active" | "complete";

interface ProcessingPanelProps {
  activeStageIndex: number;
  stageProgress: number;
}

function getStageStatus(index: number, activeIndex: number): StageStatus {
  if (index < activeIndex) return "complete";
  if (index === activeIndex) return "active";
  return "pending";
}

export default function ProcessingPanel({
  activeStageIndex,
  stageProgress,
}: ProcessingPanelProps) {
  return (
    <div className="mx-auto w-full max-w-xl">
      <SectionReveal delay={0.04} className="mb-10 text-center">
        <p className="mb-3 text-sm font-medium uppercase tracking-widest text-blue-400">
          Processing
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          Lumina is analyzing your video
        </h1>
        <p className="mx-auto mt-4 max-w-md text-base text-neutral-400">
          Fusing speech, visuals, and context through our multimodal pipeline.
        </p>
      </SectionReveal>

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
        className="relative overflow-hidden rounded-[1.6rem] border border-white/[0.08] bg-white/[0.03] p-6 shadow-[0_24px_90px_rgba(0,0,0,0.22)] backdrop-blur-xl sm:p-8"
        role="status"
        aria-live="polite"
      >
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-blue-400/40 to-transparent" />

        <ul className="space-y-5">
          {PIPELINE_STAGES.map((stage, index) => {
            const status = getStageStatus(index, activeStageIndex);
            const progress =
              status === "complete"
                ? 100
                : status === "active"
                  ? stageProgress
                  : 0;

            return (
              <PipelineStageRow
                key={stage.id}
                stage={stage}
                status={status}
                progress={progress}
                index={index}
              />
            );
          })}
        </ul>

        <motion.div
          className="mt-8 h-1 overflow-hidden rounded-full bg-white/[0.06]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-blue-500 to-sky-400"
            animate={{
              width: `${((activeStageIndex + stageProgress / 100) / PIPELINE_STAGES.length) * 100}%`,
            }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          />
        </motion.div>
      </motion.div>
    </div>
  );
}

function PipelineStageRow({
  stage,
  status,
  progress,
  index,
}: {
  stage: { id: PipelineStageId; label: string };
  status: StageStatus;
  progress: number;
  index: number;
}) {
  return (
    <motion.li
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: index * 0.05 }}
      className="relative"
    >
      <div className="flex items-center gap-4">
        <div
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border transition-all duration-300 ${
            status === "complete"
              ? "border-blue-400/40 bg-blue-500/20 text-blue-300"
              : status === "active"
                ? "border-blue-400/60 bg-blue-500/10 text-blue-400"
                : "border-white/[0.08] bg-white/[0.02] text-neutral-600"
          }`}
        >
          {status === "complete" ? (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 400, damping: 20 }}
            >
              <Check size={14} strokeWidth={2.5} />
            </motion.div>
          ) : status === "active" ? (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            >
              <Circle size={14} className="fill-blue-400/30" />
            </motion.div>
          ) : (
            <Circle size={14} />
          )}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <p
              className={`text-sm font-medium transition-colors ${
                status === "pending" ? "text-neutral-500" : "text-white"
              }`}
            >
              {stage.label}
            </p>
            {status !== "pending" && (
              <motion.span
                key={progress}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-xs tabular-nums text-neutral-500"
              >
                {Math.round(progress)}%
              </motion.span>
            )}
          </div>

          <div className="mt-2 h-1 overflow-hidden rounded-full bg-white/[0.05]">
            <motion.div
              className={`h-full rounded-full ${
                status === "complete"
                  ? "bg-blue-400"
                  : "bg-gradient-to-r from-blue-500 to-sky-400"
              }`}
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.25, ease: "easeOut" }}
            />
          </div>
        </div>
      </div>

      {status === "active" && (
        <motion.div
          className="pointer-events-none absolute -inset-x-2 -inset-y-1 rounded-xl bg-blue-500/[0.04]"
          animate={{ opacity: [0.4, 0.8, 0.4] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        />
      )}
    </motion.li>
  );
}
