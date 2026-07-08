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
                  isComplete ? "bg-[#365f53]/50" : "bg-neutral-200"
                }`}
              />
            )}
            <Link href={step.href}>
              <motion.span
                whileHover={{ scale: 1.02 }}
                className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition sm:text-sm ${
                  isCurrent
                    ? "border-[#365f53]/25 bg-[#365f53]/10 text-[#365f53] shadow-sm"
                    : isComplete
                      ? "border-neutral-200 bg-white/70 text-neutral-600 hover:border-neutral-300 hover:text-neutral-950"
                      : "border-neutral-200 bg-white/50 text-neutral-500"
                }`}
              >
                {isComplete ? (
                  <span className="flex h-4 w-4 items-center justify-center rounded-full bg-[#365f53]/10 text-[#365f53]">
                    <Check size={10} strokeWidth={3} />
                  </span>
                ) : (
                  <span
                    className={`flex h-4 w-4 items-center justify-center rounded-full text-[10px] ${
                      isCurrent
                        ? "bg-[#365f53] text-white"
                        : "bg-neutral-100 text-neutral-500"
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
