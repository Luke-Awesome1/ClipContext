"use client";

import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle } from "lucide-react";
import {
  PIPELINE_STAGE_LABELS,
  PIPELINE_STAGE_ORDER,
  type PipelineStageId,
} from "@/types/video";

interface ProcessingPanelProps {
  currentStage: PipelineStageId;
  message: string;
  error: string | null;
}

export default function ProcessingPanel({
  currentStage,
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

  // Only a three-slot window around the active stage is ever mounted —
  // the previous stage (small, fading out above), the active stage
  // (large and bold, centred), and the next stage (small preview below).
  // As the stage advances, each slot's contents slide into the next via
  // layout animation instead of the list growing downward — this keeps
  // the panel's height constant so nothing ever needs to scroll.
  const currentIndex = PIPELINE_STAGE_ORDER.indexOf(currentStage);
  const windowEntries = PIPELINE_STAGE_ORDER.map((id, index) => ({ id, index })).filter(
    ({ index }) => Math.abs(index - currentIndex) <= 1,
  );

  return (
    <div
      className="mx-auto flex min-h-[60vh] w-full max-w-2xl flex-col items-center justify-center px-5 py-12 text-center"
      role="status"
      aria-live="polite"
    >
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="mb-12 text-xs font-medium uppercase tracking-[0.3em] text-[#365f53]"
      >
        Processing
      </motion.p>

      <div className="flex w-full flex-col items-center justify-center gap-4">
        <AnimatePresence mode="popLayout" initial={false}>
          {windowEntries.map(({ id, index }) => {
            const distance = index - currentIndex;
            const isActive = distance === 0;

            return (
              <motion.div
                key={id}
                layout="position"
                initial={{ opacity: 0, y: distance <= 0 ? -28 : 28 }}
                animate={{ opacity: isActive ? 1 : 0.35, y: 0 }}
                exit={{ opacity: 0, y: -28 }}
                transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                className="flex flex-col items-center"
              >
                <p
                  className={`font-semibold leading-tight transition-all duration-500 ease-out ${
                    isActive
                      ? "text-3xl text-neutral-950 sm:text-5xl"
                      : "text-sm text-neutral-400 sm:text-base"
                  }`}
                >
                  {PIPELINE_STAGE_LABELS[id]}
                </p>

                {isActive && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.4, delay: 0.2 }}
                    className="mt-3 text-sm text-neutral-500 sm:text-base"
                  >
                    {message}
                  </motion.p>
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
