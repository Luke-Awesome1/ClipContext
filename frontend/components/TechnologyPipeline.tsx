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
    title: "Upload",
    subtitle: "Video",
    description: "Upload a short-form video or provide creator context through an optional YouTube channel.",
    icon: FileText,
    accent: "from-cyan-400/30 via-sky-400/10 to-transparent",
    symbol: "✦",
    chip: "Start",
  },
  {
    title: "Creator Profiling",
    subtitle: "Style profile",
    description: "Analyze the creator's previous 50 uploads to understand writing style, tone, formatting and publishing habits.",
    icon: Sparkles,
    accent: "from-violet-400/30 via-fuchsia-400/10 to-transparent",
    symbol: "◌",
    chip: "Learn",
  },
  {
    title: "Multimodal Understanding",
    subtitle: "Speech + frames",
    description: "Understand speech, visual frames, scene context and on-screen text to build a complete picture of the video.",
    icon: Workflow,
    accent: "from-blue-400/30 via-indigo-400/10 to-transparent",
    symbol: "◐",
    chip: "Sense",
  },
  {
    title: "Trend Intelligence",
    subtitle: "What works",
    description: "Analyze high-performing videos from the same niche to identify title patterns, description structure and audience preferences.",
    icon: BrainCircuit,
    accent: "from-emerald-400/30 via-cyan-400/10 to-transparent",
    symbol: "◍",
    chip: "Trend",
  },
  {
    title: "Generate & Publish",
    subtitle: "Ready to ship",
    description: "Generate optimized title, description and hashtags across four writing styles ready for publishing.",
    icon: ArrowRight,
    accent: "from-amber-400/30 via-orange-400/10 to-transparent",
    symbol: "↗",
    chip: "Ship",
  },
];

const technologyPillars = [
  {
    title: "Creator Understanding",
    text: "Uses previous uploads to learn the creator's unique writing style instead of generating generic captions.",
  },
  {
    title: "Multimodal Intelligence",
    text: "Combines speech transcription, frame understanding and contextual reasoning into a unified representation.",
  },
  {
    title: "Trend Intelligence",
    text: "Analyzes high-performing videos within the same niche to surface patterns that increase discoverability.",
  },
  {
    title: "Platform Optimization",
    text: "Generates publishing assets tailored for YouTube and Instagram instead of generic social media text.",
  },
  {
    title: "Personalized Generation",
    text: "Balances historical creator style with current platform trends to produce work that feels authentic and competitive.",
  },
  {
    title: "Future Ready",
    text: "Built to support additional platforms, languages and AI models with minimal changes.",
  },
];

export default function TechnologyPipeline() {
  return (
    <>
      <section id="pipeline" className="relative py-16 sm:py-20">
        <div className="mx-auto max-w-6xl px-5 sm:px-8">
          <SectionReveal delay={0.04} className="mb-10 max-w-3xl">
            <p className="mb-3 text-sm font-medium uppercase tracking-[0.28em] text-blue-400">
              Pipeline
            </p>
            <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
              A creator-first flow from upload to publish.
            </h2>
            <p className="mt-4 text-base leading-7 text-neutral-400 sm:text-lg">
              ClipContext learns the creator, interprets the video, and turns that into publishing assets that feel personal and discoverable.
            </p>
          </SectionReveal>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.25, margin: "-60px" }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            className="relative overflow-hidden rounded-[2rem] border border-white/[0.08] bg-white/[0.03] p-4 shadow-[0_25px_100px_rgba(0,0,0,0.35)] backdrop-blur-2xl sm:p-6 lg:p-8"
          >
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.16),transparent_38%),radial-gradient(circle_at_bottom_right,rgba(125,211,252,0.12),transparent_33%)]" />
            <div className="pointer-events-none absolute -left-12 top-8 h-36 w-36 rounded-full bg-cyan-400/10 blur-3xl" />
            <div className="pointer-events-none absolute -bottom-8 right-8 h-44 w-44 rounded-full bg-blue-500/10 blur-3xl" />

            <div className="relative grid gap-3 lg:grid-cols-5">
              {pipelineSteps.map((step, index) => {
                const Icon = step.icon;
                return (
                  <motion.div
                    key={step.title}
                    whileHover={{ y: -6, scale: 1.01, boxShadow: "0 20px 50px rgba(59,130,246,0.16)" }}
                    transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
                    className="group relative overflow-hidden rounded-[1.35rem] border border-white/[0.08] bg-[#0D1113]/85 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]"
                  >
                    <div className={`absolute inset-0 bg-gradient-to-br ${step.accent}`} />
                    <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/40 to-transparent" />

                    <div className="relative mb-4 flex items-center justify-between">
                      <div className="inline-flex rounded-full border border-white/[0.08] bg-white/[0.04] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.24em] text-neutral-500">
                        0{index + 1}
                      </div>
                      <motion.div
                        className="rounded-2xl border border-blue-400/20 bg-blue-500/10 p-2 text-blue-400"
                        animate={{ y: [0, -2, 0], rotate: [0, 3, 0] }}
                        transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut", delay: index * 0.18 }}
                      >
                        <Icon size={16} />
                      </motion.div>
                    </div>

                    <motion.div
                      className="relative mb-3 flex h-9 w-9 items-center justify-center rounded-full border border-white/[0.08] bg-white/[0.05] text-lg text-slate-200"
                      animate={{ scale: [1, 1.04, 1], opacity: [0.8, 1, 0.8] }}
                      transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut", delay: index * 0.16 }}
                    >
                      {step.symbol}
                    </motion.div>

                    <div className="relative">
                      <div className="inline-flex rounded-full border border-white/[0.08] bg-white/[0.04] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-400">
                        {step.chip}
                      </div>
                      <h3 className="mt-3 text-base font-semibold text-white">{step.title}</h3>
                      <p className="mt-1 text-sm font-medium text-blue-300">{step.subtitle}</p>
                      <p className="mt-3 text-sm leading-6 text-neutral-400">{step.description}</p>
                    </div>
                  </motion.div>
                );
              })}
            </div>

            <div className="relative mt-5 flex flex-wrap gap-3">
              <div className="rounded-full border border-white/[0.08] bg-white/[0.04] px-3 py-1.5 text-sm text-neutral-400 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
                Learns from creator history and current niche trends.
              </div>
              <div className="rounded-full border border-white/[0.08] bg-white/[0.04] px-3 py-1.5 text-sm text-neutral-400 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
                Produces title, description and hashtag sets for publishing.
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <section id="technology" className="relative pb-16 sm:pb-20">
        <div className="mx-auto max-w-6xl px-5 sm:px-8">
          <SectionReveal delay={0.06} className="mb-8 max-w-3xl">
            <p className="mb-3 text-sm font-medium uppercase tracking-[0.28em] text-blue-400">
              Technology
            </p>
            <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
              Why ClipContext produces better outputs.
            </h2>
            <p className="mt-4 text-base leading-7 text-neutral-400 sm:text-lg">
              It connects creator identity, video context and trend signals so the output feels specific rather than generic.
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
                className="rounded-[1.25rem] border border-white/[0.08] bg-white/[0.03] p-6 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] backdrop-blur-sm"
              >
                <p className="text-sm font-semibold text-white">{pillar.title}</p>
                <p className="mt-2 text-sm leading-6 text-neutral-400">{pillar.text}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
