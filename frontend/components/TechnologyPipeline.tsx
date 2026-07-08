"use client";

import { motion } from "framer-motion";
import {
  ArrowRight,
  BrainCircuit,
  FileText,
  MessageSquare,
  Eye,
  Sparkles,
  Workflow,
} from "lucide-react";
import SectionReveal from "@/components/ui/SectionReveal";

const pipelineSteps = [
  {
    title: "Validate",
    subtitle: "Short video",
    description: "Accept a creator video, validate the file, and prepare deterministic output folders for cached artifacts.",
    icon: FileText,
    accent: "from-neutral-200 via-white/60 to-transparent",
    symbol: "01",
    chip: "Start",
  },
  {
    title: "Transcribe",
    subtitle: "Audio",
    description: "Extract audio locally and build the transcript used as the factual speech source for later generation.",
    icon: Sparkles,
    accent: "from-stone-200 via-white/60 to-transparent",
    symbol: "02",
    chip: "Listen",
  },
  {
    title: "Select Windows",
    subtitle: "Sparse frames",
    description: "Scan at 1 FPS, score local quality and diversity, then select representative 5-second visual windows.",
    icon: Workflow,
    accent: "from-emerald-100 via-white/60 to-transparent",
    symbol: "03",
    chip: "Sample",
  },
  {
    title: "Build Context",
    subtitle: "VideoContext",
    description: "Fuse transcript and visual analysis into topic, core message, visible text, key moments and uncertainty fields.",
    icon: BrainCircuit,
    accent: "from-zinc-200 via-white/60 to-transparent",
    symbol: "04",
    chip: "Fuse",
  },
  {
    title: "Generate Sets",
    subtitle: "Publish assets",
    description: "Use platform syntax to produce exactly 10 titles, 10 descriptions and 10 hashtag sets.",
    icon: ArrowRight,
    accent: "from-lime-100 via-white/60 to-transparent",
    symbol: "05",
    chip: "Ship",
  },
];

const technologyPillars = [
  {
    title: "Deterministic artifacts",
    text: "The backend stores transcription, visual timeline, VideoContext, trend syntax, generated content and audit outputs by video ID.",
  },
  {
    title: "Sparse multimodal budget",
    text: "The pipeline reduces redundant frame inference by selecting representative temporal windows before paid model calls.",
  },
  {
    title: "Schema-validated generation",
    text: "Generated output must pass Pydantic validation: 10 ordered titles, 10 descriptions and 10 hashtag arrays.",
  },
  {
    title: "Platform syntax",
    text: "Trend and creator analysis inform structure and vocabulary, while VideoContext remains the factual source of truth.",
  },
  {
    title: "Grounding guardrails",
    text: "The content prompt prevents unsupported people, places, claims, brands, objects and events.",
  },
  {
    title: "Provider flexibility",
    text: "Visual understanding and text generation can move between providers while preserving the canonical context contract.",
  },
];

export default function TechnologyPipeline() {
  return (
    <>
      <section id="pipeline" className="relative py-16 sm:py-20">
        <div className="mx-auto max-w-6xl px-5 sm:px-8">
          <SectionReveal delay={0.04} className="mb-10 max-w-3xl">
            <p className="mb-3 text-sm font-medium uppercase tracking-[0.28em] text-[#365f53]">
              Pipeline
            </p>
            <h2 className="text-3xl font-semibold tracking-tight text-neutral-950 sm:text-4xl">
              The pipeline the backend is actually running.
            </h2>
            <p className="mt-4 text-base leading-7 text-neutral-600 sm:text-lg">
              Each stage maps to a concrete backend artifact, from local
              transcription through sparse visual windows to schema-validated
              generated content.
            </p>
          </SectionReveal>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.25, margin: "-60px" }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            className="relative overflow-hidden rounded-lg border border-neutral-200 bg-white/70 p-4 shadow-sm backdrop-blur-2xl sm:p-6 lg:p-8"
          >
            <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-neutral-200" />

            <div className="relative grid gap-3 lg:grid-cols-5">
              {pipelineSteps.map((step, index) => {
                const Icon = step.icon;
                return (
                  <motion.div
                    key={step.title}
                    whileHover={{ y: -4, scale: 1.01, boxShadow: "0 12px 28px rgba(23,23,23,0.08)" }}
                    transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
                    className="group relative overflow-hidden rounded-lg border border-neutral-200 bg-[#faf9f6] p-4 shadow-sm"
                  >
                    <div className={`absolute inset-0 bg-gradient-to-br ${step.accent}`} />
                    <div className="absolute inset-x-0 top-0 h-px bg-neutral-200" />

                    <div className="relative mb-4 flex items-center justify-between">
                      <div className="inline-flex rounded-full border border-neutral-200 bg-white px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.24em] text-neutral-500">
                        0{index + 1}
                      </div>
                      <motion.div
                        className="rounded-lg border border-[#365f53]/20 bg-[#365f53]/10 p-2 text-[#365f53]"
                        animate={{ y: [0, -2, 0], rotate: [0, 3, 0] }}
                        transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut", delay: index * 0.18 }}
                      >
                        <Icon size={16} />
                      </motion.div>
                    </div>

                    <motion.div
                      className="relative mb-3 flex h-9 w-9 items-center justify-center rounded-full border border-neutral-200 bg-white text-xs font-semibold text-neutral-700"
                      animate={{ scale: [1, 1.04, 1], opacity: [0.8, 1, 0.8] }}
                      transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut", delay: index * 0.16 }}
                    >
                      {step.symbol}
                    </motion.div>

                    <div className="relative">
                      <div className="inline-flex rounded-full border border-neutral-200 bg-white px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.24em] text-neutral-500">
                        {step.chip}
                      </div>
                      <h3 className="mt-3 text-base font-semibold text-neutral-950">{step.title}</h3>
                      <p className="mt-1 text-sm font-medium text-[#365f53]">{step.subtitle}</p>
                      <p className="mt-3 text-sm leading-6 text-neutral-600">{step.description}</p>
                    </div>
                  </motion.div>
                );
              })}
            </div>

            <div className="relative mt-5 flex flex-wrap gap-3">
              <div className="rounded-full border border-neutral-200 bg-white px-3 py-1.5 text-sm text-neutral-600 shadow-sm">
                Caches each expensive stage by generated video ID.
              </div>
              <div className="rounded-full border border-neutral-200 bg-white px-3 py-1.5 text-sm text-neutral-600 shadow-sm">
                Produces ordered title, description and hashtag candidates.
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <section id="technology" className="relative pb-16 sm:pb-20">
        <div className="mx-auto max-w-6xl px-5 sm:px-8">
          <SectionReveal delay={0.06} className="mb-8 max-w-3xl">
            <p className="mb-3 text-sm font-medium uppercase tracking-[0.28em] text-[#365f53]">
              Technology
            </p>
            <h2 className="text-3xl font-semibold tracking-tight text-neutral-950 sm:text-4xl">
              Why the output stays grounded.
            </h2>
            <p className="mt-4 text-base leading-7 text-neutral-600 sm:text-lg">
              VideoContext is the factual contract. Trend syntax shapes the
              writing, but it cannot invent facts that are not in the analyzed
              video.
            </p>
          </SectionReveal>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {technologyPillars.map((pillar) => (
              <motion.div
                key={pillar.title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5 }}
                className="rounded-lg border border-neutral-200 bg-white/70 p-6 shadow-sm backdrop-blur-sm"
              >
                <p className="text-sm font-semibold text-neutral-950">{pillar.title}</p>
                <p className="mt-2 text-sm leading-6 text-neutral-600">{pillar.text}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
