"use client";

import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  Brain,
  Check,
  CheckCircle2,
  Clock,
  Eye,
  Film,
  Globe,
  Layers,
  ListOrdered,
  ShieldCheck,
  Sparkles,
  Subtitles,
  Users,
  Volume2,
  type LucideIcon,
} from "lucide-react";
import {
  PIPELINE_STAGE_LABELS,
  PIPELINE_STAGE_ORDER,
  type PipelineStageId,
} from "@/types/video";

interface ProcessingPanelProps {
  currentStage: PipelineStageId;
  message: string;
  error: string | null;
  progress?: number;
}

const STAGE_ICONS: Record<PipelineStageId, LucideIcon> = {
  queued: Clock,
  validating: ShieldCheck,
  extracting_audio: Volume2,
  extracting_frames: Film,
  transcribing: Subtitles,
  temporal_alignment: Layers,
  visual_analysis: Eye,
  context_generation: Brain,
  worldwide_trends: Globe,
  creator_trends: Users,
  content_generation: Sparkles,
  ranking: ListOrdered,
  completed: CheckCircle2,
};

export default function ProcessingPanel({
  currentStage,
  message,
  error,
  progress = 0,
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

  const currentIndex = PIPELINE_STAGE_ORDER.indexOf(currentStage);
  const isComplete = currentStage === "completed";
  const Icon = STAGE_ICONS[currentStage] ?? Sparkles;

  // The backend's "message" for the completed stage ("Pipeline complete")
  // just restates the "Complete" heading below it — show something more
  // useful there instead of the same idea twice.
  const displayMessage = isComplete ? "Redirecting to your results..." : message;

  return (
    <div
      className="mx-auto w-full max-w-2xl rounded-lg border border-neutral-200 bg-white/70 p-8 shadow-sm backdrop-blur-xl sm:p-10"
      role="status"
      aria-live="polite"
    >
      <div className="mb-8 flex items-center justify-between gap-4">
        <p className="text-xs font-medium uppercase tracking-[0.3em] text-[#365f53]">
          Processing
        </p>
        <p className="text-xs font-semibold tabular-nums text-neutral-500">
          {Math.round(progress)}%
        </p>
      </div>

      <div className="mb-10 h-1.5 w-full overflow-hidden rounded-full bg-neutral-200">
        <motion.div
          className="h-full rounded-full bg-[#365f53]"
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>

      <div className="flex min-h-[7rem] flex-col items-center justify-center text-center">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStage}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="flex flex-col items-center"
          >
            <div
              className={`mb-4 flex h-14 w-14 items-center justify-center rounded-full border ${
                isComplete
                  ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-600"
                  : "border-[#365f53]/20 bg-[#365f53]/10 text-[#365f53]"
              }`}
            >
              <motion.div
                animate={isComplete ? {} : { rotate: 360 }}
                transition={
                  isComplete
                    ? undefined
                    : { duration: 2.2, repeat: Infinity, ease: "linear" }
                }
              >
                <Icon size={24} strokeWidth={1.75} />
              </motion.div>
            </div>

            <p className="text-xl font-semibold leading-tight text-neutral-950 sm:text-2xl">
              {PIPELINE_STAGE_LABELS[currentStage]}
            </p>
            <p className="mt-2 text-sm text-neutral-500 sm:text-base">
              {displayMessage}
            </p>
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="mt-10 flex flex-wrap items-center justify-center gap-2 border-t border-neutral-200 pt-8">
        {PIPELINE_STAGE_ORDER.map((id, index) => {
          const StageIcon = STAGE_ICONS[id];
          const stageIsComplete = index < currentIndex || isComplete;
          const stageIsCurrent = id === currentStage;

          return (
            <div
              key={id}
              title={PIPELINE_STAGE_LABELS[id]}
              className={`flex h-7 w-7 items-center justify-center rounded-full border transition-colors duration-300 ${
                stageIsCurrent
                  ? "border-[#365f53]/40 bg-[#365f53] text-white shadow-sm"
                  : stageIsComplete
                    ? "border-[#365f53]/20 bg-[#365f53]/10 text-[#365f53]"
                    : "border-neutral-200 bg-white text-neutral-300"
              }`}
            >
              {stageIsComplete && !stageIsCurrent ? (
                <Check size={12} strokeWidth={3} />
              ) : (
                <StageIcon size={12} strokeWidth={2} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
