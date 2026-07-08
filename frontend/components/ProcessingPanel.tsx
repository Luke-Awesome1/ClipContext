"use client";

import { motion } from "framer-motion";
import { AlertTriangle, Check, Circle } from "lucide-react";
import {
  PIPELINE_STAGE_LABELS,
  PIPELINE_STAGE_ORDER,
  type PipelineStageId,
} from "@/types/video";
import SectionReveal from "@/components/ui/SectionReveal";

type StageStatus = "pending" | "active" | "complete";

interface ProcessingPanelProps {
  currentStage: PipelineStageId;
  progress: number;
  message: string;
  error: string | null;
}

function getStageStatus(
  stage: PipelineStageId,
  currentStage: PipelineStageId,
): StageStatus {
  const currentIndex = PIPELINE_STAGE_ORDER.indexOf(currentStage);
  const stageIndex = PIPELINE_STAGE_ORDER.indexOf(stage);
  if (stageIndex < currentIndex) return "complete";
  if (stageIndex === currentIndex) return "active";
  return "pending";
}

const VISIBLE_STAGES = PIPELINE_STAGE_ORDER.filter((id) => id !== "completed");

export default function ProcessingPanel({
  currentStage,
  progress,
  message,
  error,
}: ProcessingPanelProps) {
  return (
    <div className="mx-auto w-full max-w-xl">
      <SectionReveal delay={0.04} className="mb-10 text-center">
        <p className="mb-3 text-sm font-medium uppercase tracking-widest text-[#365f53]">
          Processing
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-neutral-950 sm:text-4xl">
          ClipContext is building video context
        </h1>
        <p className="mx-auto mt-4 max-w-md text-base text-neutral-600">
          {error ?? message}
        </p>
      </SectionReveal>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"
        >
          <AlertTriangle size={18} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </motion.div>
      )}

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
        className="relative overflow-hidden rounded-lg border border-neutral-200 bg-white/75 p-6 shadow-sm backdrop-blur-xl sm:p-8"
        role="status"
        aria-live="polite"
      >
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-neutral-200" />

        <ul className="space-y-5">
          {VISIBLE_STAGES.map((stageId, index) => {
            const status = getStageStatus(stageId, currentStage);

            return (
              <PipelineStageRow
                key={stageId}
                label={PIPELINE_STAGE_LABELS[stageId]}
                status={status}
                index={index}
              />
            );
          })}
        </ul>

        <motion.div
          className="mt-8 h-1 overflow-hidden rounded-full bg-neutral-200"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <motion.div
            className="h-full rounded-full bg-[#365f53]"
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          />
        </motion.div>
      </motion.div>
    </div>
  );
}

function PipelineStageRow({
  label,
  status,
  index,
}: {
  label: string;
  status: StageStatus;
  index: number;
}) {
  return (
    <motion.li
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: index * 0.03 }}
      className="relative"
    >
      <div className="flex items-center gap-4">
        <div
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border transition-all duration-300 ${
            status === "complete"
              ? "border-[#365f53]/35 bg-[#365f53]/10 text-[#365f53]"
              : status === "active"
                ? "border-[#365f53]/50 bg-[#365f53]/10 text-[#365f53]"
                : "border-neutral-200 bg-white text-neutral-500"
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
              <Circle size={14} className="fill-[#365f53]/20" />
            </motion.div>
          ) : (
            <Circle size={14} />
          )}
        </div>

        <div className="min-w-0 flex-1">
          <p
            className={`text-sm font-medium transition-colors ${
              status === "pending" ? "text-neutral-500" : "text-neutral-950"
            }`}
          >
            {label}
          </p>
        </div>
      </div>

      {status === "active" && (
        <motion.div
          className="pointer-events-none absolute -inset-x-2 -inset-y-1 rounded-lg bg-[#365f53]/[0.04]"
          animate={{ opacity: [0.4, 0.8, 0.4] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        />
      )}
    </motion.li>
  );
}
