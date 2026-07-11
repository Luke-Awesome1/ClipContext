"use client";

import { motion } from "framer-motion";
import { Brain, CheckCircle2, Eye, MessageSquare } from "lucide-react";
import SectionReveal from "@/components/ui/SectionReveal";

const features = [
  {
    icon: MessageSquare,
    title: "Local Speech Context",
    description:
      "Extracts audio and transcription before generation so the spoken message anchors the output.",
  },
  {
    icon: Eye,
    title: "Sparse Visual Evidence",
    description:
      "Scans frames locally, selects diverse temporal windows, and avoids sending redundant video context downstream.",
  },
  {
    icon: Brain,
    title: "Canonical VideoContext",
    description:
      "Fuses transcript, visuals, visible text, key moments, uncertainty, style, and audience signals into one schema.",
  },
  {
    icon: CheckCircle2,
    title: "Candidate Sets",
    description:
      "Generates 10 titles, 10 descriptions, and 10 hashtag sets from verified context and platform syntax, then ranks and surfaces the top 5 of each.",
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
          <p className="mb-3 text-sm font-medium uppercase tracking-[0.24em] text-[#365f53]">
            Features
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-neutral-950 sm:text-4xl">
            Built around the backend artifacts.
          </h2>
          <p className="mt-4 text-base leading-relaxed text-neutral-600 sm:text-lg">
            The interface reflects the actual flow: validation, transcription,
            sparse frame selection, VideoContext construction, and grounded
            content generation.
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
              className="group relative overflow-hidden rounded-lg border border-neutral-200 bg-white/70 p-7 shadow-sm backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:border-[#365f53]/25 hover:bg-white"
            >
              <div className="pointer-events-none absolute inset-x-4 top-0 h-px rounded-full bg-neutral-200" />

              <div className="relative">
                <div className="mb-5 inline-flex rounded-lg border border-neutral-200 bg-[#f6f5f2] p-3 text-[#365f53] transition-all duration-300 group-hover:-translate-y-0.5 group-hover:border-[#365f53]/25">
                  <feature.icon size={22} strokeWidth={1.75} />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-neutral-950">
                  {feature.title}
                </h3>
                <p className="text-sm leading-relaxed text-neutral-600">
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
