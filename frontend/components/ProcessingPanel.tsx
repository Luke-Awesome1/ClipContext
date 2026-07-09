"use client";

import { motion } from "framer-motion";
import { AlertTriangle } from "lucide-react";
import {
  PIPELINE_STAGE_LABELS,
  PIPELINE_STAGE_ORDER,
  type PipelineStageId,
} from "@/types/video";

interface ProcessingPanelProps {
  currentStage: PipelineStageId;
  progress: number;
  message: string;
  error: string | null;
}

const VISIBLE_STAGES = PIPELINE_STAGE_ORDER.filter((id) => id !== "completed");

// The line grows first; the next step's label fades in as the line
// finishes reaching it — mirrors a film credits roll / step-by-step
// reasoning reveal rather than a static checklist.
const LINE_DURATION = 0.5;
const LABEL_DELAY = 0.4;

export default function ProcessingPanel({
  currentStage,
  progress,
  message,
  error,
}: ProcessingPanelProps) {
  if (error) {
    return (
      <div className="mx-auto flex min-h-[50vh] w-full max-w-lg flex-col items-center justify-center gap-4 px-5 text-center">
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"
        >
          <AlertTriangle size={18} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </motion.div>
      </div>
    );
  }

  const isComplete = currentStage === "completed";
  const activeIndex = isComplete ? -1 : VISIBLE_STAGES.indexOf(currentStage);
  const revealedCount = isComplete
    ? VISIBLE_STAGES.length
    : Math.max(activeIndex + 1, 1);
  const revealedStages = VISIBLE_STAGES.slice(0, revealedCount);

  return (
    <div
      className="mx-auto flex min-h-[50vh] w-full max-w-lg flex-col items-center justify-center px-5 py-12 text-center"
      role="status"
      aria-live="polite"
    >
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="mb-10 text-xs font-medium uppercase tracking-[0.3em] text-[#365f53]"
      >
        Processing
      </motion.p>

      <div className="flex flex-col items-center">
        {revealedStages.map((stageId, index) => {
          const isActive = index === activeIndex;

          return (
            <div key={stageId} className="flex flex-col items-center">
              {index > 0 && (
                <motion.div
                  initial={{ scaleY: 0 }}
                  animate={{ scaleY: 1 }}
                  transition={{ duration: LINE_DURATION, ease: "easeInOut" }}
                  style={{ transformOrigin: "top" }}
                  className="h-8 w-px bg-neutral-300"
                />
              )}

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  duration: 0.5,
                  delay: index > 0 ? LABEL_DELAY : 0,
                  ease: [0.16, 1, 0.3, 1],
                }}
                className="flex flex-col items-center py-1.5"
              >
                <p
                  className={`font-medium leading-snug transition-all duration-500 ease-out ${
                    isActive ? "text-xl text-neutral-950 sm:text-2xl" : "text-sm text-neutral-400"
                  }`}
                >
                  {PIPELINE_STAGE_LABELS[stageId]}
                </p>

                {isActive && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.4, delay: 0.15 }}
                    className="mt-2 text-xs text-neutral-500"
                  >
                    {message}
                  </motion.p>
                )}
              </motion.div>
            </div>
          );
        })}
      </div>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4 }}
        className="mt-10 text-xs tabular-nums text-neutral-400"
      >
        {isComplete ? "Complete" : `${progress}%`}
      </motion.p>
    </div>
  );
}
