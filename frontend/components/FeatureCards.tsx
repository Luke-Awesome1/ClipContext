"use client";

import { motion } from "framer-motion";
import { Brain, Layers, Palette, ScanEye } from "lucide-react";
import SectionReveal from "@/components/ui/SectionReveal";

const features = [
  {
    icon: Brain,
    title: "Multimodal AI",
    description:
      "Processes audio and visual frames in parallel — understanding what's said and what's shown, together.",
  },
  {
    icon: Layers,
    title: "Unified AI Understanding",
    description:
      "Fuses speech, scene context, and on-screen elements into a single coherent model of your content.",
  },
  {
    icon: Palette,
    title: "Four Caption Styles",
    description:
      "Formal, Sarcastic, Humor-T, and Humor-NT — each tuned for a different audience and platform.",
  },
  {
    icon: ScanEye,
    title: "Context Aware Generation",
    description:
      "Titles and captions adapt to pacing, tone, and visual cues so every output feels native to your video.",
  },
];

const container = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.12 },
  },
};

const card = {
  hidden: { opacity: 0, y: 28 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, ease: [0.16, 1, 0.3, 1] as const },
  },
};

export default function FeatureCards() {
  return (
    <section id="features" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <SectionReveal delay={0.05} className="mb-16 max-w-2xl">
          <p className="mb-3 text-sm font-medium uppercase tracking-[0.24em] text-blue-400">
            Features
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            Intelligence that sees the full picture.
          </h2>
          <p className="mt-4 text-base leading-relaxed text-neutral-400 sm:text-lg">
            Most tools only transcribe speech. ClipContext understands your video
            holistically — so every caption carries real context.
          </p>
        </SectionReveal>

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2, margin: "-80px" }}
          className="grid gap-5 sm:grid-cols-2"
        >
          {features.map((feature) => (
            <motion.div
              key={feature.title}
              variants={card}
              whileHover={{ y: -4, rotate: -0.4, scale: 1.01, transition: { duration: 0.2 } }}
              className="group relative overflow-hidden rounded-[1.5rem] border border-white/[0.08] bg-white/[0.03] p-7 shadow-[0_20px_60px_rgba(0,0,0,0.22)] backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:border-blue-400/20 hover:bg-white/[0.05]"
            >
              <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-blue-500/0 via-transparent to-blue-500/0 opacity-0 transition-opacity duration-500 group-hover:opacity-100 group-hover:from-blue-500/[0.06]" />
              <div className="pointer-events-none absolute inset-x-4 top-0 h-px rounded-full bg-gradient-to-r from-transparent via-white/25 to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />

              <div className="relative">
                <div className="mb-5 inline-flex rounded-xl border border-white/[0.08] bg-white/[0.05] p-3 text-blue-400 transition-all duration-300 group-hover:-translate-y-0.5 group-hover:border-blue-400/20 group-hover:bg-blue-500/10">
                  <feature.icon size={22} strokeWidth={1.75} />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-white">
                  {feature.title}
                </h3>
                <p className="text-sm leading-relaxed text-neutral-400">
                  {feature.description}
                </p>
              </div>
            </motion.div>
          ))}
        </motion.div>

      </div>
    </section>
  );
}
