"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Check } from "lucide-react";

const steps = [
  { id: "landing", label: "Landing", href: "/" },
  { id: "upload", label: "Upload", href: "/#upload" },
  { id: "processing", label: "Processing", href: "/process" },
  { id: "results", label: "Results", href: "/results" },
] as const;

type StepId = (typeof steps)[number]["id"];

interface JourneyStepperProps {
  current: StepId;
}

export default function JourneyStepper({ current }: JourneyStepperProps) {
  const currentIndex = steps.findIndex((s) => s.id === current);

  return (
    <nav
      aria-label="Progress"
      className="mx-auto mb-12 flex max-w-2xl flex-wrap items-center justify-center gap-2 sm:gap-0"
    >
      {steps.map((step, index) => {
        const isComplete = index < currentIndex;
        const isCurrent = index === currentIndex;

        return (
          <div key={step.id} className="flex items-center">
            {index > 0 && (
              <div
                className={`mx-2 hidden h-px w-8 sm:block md:w-12 ${
                  isComplete ? "bg-blue-400/50" : "bg-white/[0.08]"
                }`}
              />
            )}
            <Link href={step.href}>
              <motion.span
                whileHover={{ scale: 1.02 }}
                className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition sm:text-sm ${
                  isCurrent
                    ? "border-blue-400/25 bg-blue-500/15 text-blue-300 shadow-[0_0_24px_rgba(91,140,255,0.12)]"
                    : isComplete
                      ? "border-white/[0.06] bg-white/[0.04] text-neutral-400 hover:border-white/10 hover:text-white"
                      : "border-white/[0.05] bg-white/[0.02] text-neutral-600"
                }`}
              >
                {isComplete ? (
                  <span className="flex h-4 w-4 items-center justify-center rounded-full bg-blue-500/20 text-blue-400">
                    <Check size={10} strokeWidth={3} />
                  </span>
                ) : (
                  <span
                    className={`flex h-4 w-4 items-center justify-center rounded-full text-[10px] ${
                      isCurrent
                        ? "bg-blue-500 text-white"
                        : "bg-white/[0.06] text-neutral-500"
                    }`}
                  >
                    {index + 1}
                  </span>
                )}
                {step.label}
              </motion.span>
            </Link>
          </div>
        );
      })}
    </nav>
  );
}
