"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Play, Sparkles } from "lucide-react";
import { useVideoSession } from "@/context/VideoSessionContext";
import CaptionTabs, { type CandidatePool } from "@/components/CaptionTabs";

// Sample data shaped exactly like real PipelineResult output — this is a
// preview of what ClipContext generates, not a design placeholder.
const sampleTitles = [
  "I Almost Quit. Then This Happened.",
  "The Comeback Nobody Saw Coming",
  "Why I Didn't Give Up (Yet)",
];

const sampleDescription =
  "A short, honest look at the moment giving up felt easier than continuing — and why that moment passed.";

const sampleHashtags = ["#Motivation", "#ComebackStory", "#NeverGiveUp", "#ShortFilm"];

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, delay: i * 0.08, ease: [0.16, 1, 0.3, 1] as const },
  }),
};

export default function Hero() {
  const router = useRouter();
  const { startDemo } = useVideoSession();
  const [activePool, setActivePool] = useState<CandidatePool>("titles");

  const handleWatchDemo = () => {
    startDemo();
    router.push("/process");
  };

  return (
    <section className="relative overflow-hidden pt-28 pb-20 sm:pt-36 sm:pb-28">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-0 top-24 h-px w-full bg-neutral-200/70" />
        <div className="absolute bottom-10 left-0 h-px w-full bg-neutral-200/70" />
      </div>

      <div className="relative mx-auto grid max-w-6xl items-center gap-16 px-5 sm:px-8 lg:grid-cols-2 lg:gap-12">
        <motion.div initial="hidden" animate="visible" className="max-w-xl">
          <motion.div
            custom={0}
            variants={fadeUp}
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-neutral-200 bg-white/70 px-3 py-1.5 text-xs font-medium text-neutral-600 shadow-sm backdrop-blur-sm"
          >
            <Sparkles size={14} className="text-[#365f53]" />
            AI metadata for YouTube creators
          </motion.div>

          <motion.h1
            custom={1}
            variants={fadeUp}
            className="text-4xl font-semibold leading-[0.98] text-neutral-950 sm:text-5xl lg:text-[3.45rem]"
          >
            Your video already
            <br />
            <span className="text-[#365f53]">wrote the title.</span>
          </motion.h1>

          <motion.p
            custom={2}
            variants={fadeUp}
            className="mt-6 max-w-xl text-base leading-7 text-neutral-600 sm:text-lg"
          >
            Upload a clip. Get ranked titles, descriptions, and hashtags —
            grounded in what&apos;s actually said and shown.
          </motion.p>

          <motion.div
            custom={3}
            variants={fadeUp}
            className="mt-10 flex flex-wrap items-center gap-4"
          >
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Link
                href="#upload"
                className="inline-flex items-center gap-2 rounded-full bg-neutral-950 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:bg-[#365f53] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
              >
                Upload Video
                <ArrowRight size={16} />
              </Link>
            </motion.div>
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <button
                type="button"
                onClick={handleWatchDemo}
                className="inline-flex items-center gap-2 rounded-full border border-neutral-300 bg-white/70 px-6 py-3 text-sm font-semibold text-neutral-900 backdrop-blur-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-[#365f53]/30 hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
              >
                <Play size={16} className="fill-neutral-900 text-neutral-900" />
                Watch Demo
              </button>
            </motion.div>
          </motion.div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 32 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.25, ease: [0.16, 1, 0.3, 1] }}
          className="relative mx-auto w-full max-w-lg lg:max-w-none"
        >
          <motion.div
            animate={{ y: [0, -10, 0] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
            className="relative rounded-lg border border-neutral-200 bg-white/80 p-4 shadow-sm backdrop-blur-2xl sm:p-5"
          >
            <div className="relative space-y-4">
              <div className="relative aspect-video overflow-hidden rounded-lg border border-neutral-200 bg-neutral-900 shadow-sm">
                <Image
                  src="/hero.png"
                  alt="ClipContext — a multimodal Creator Intelligence platform for every creator"
                  fill
                  priority
                  sizes="(min-width: 1024px) 32rem, 100vw"
                  className="object-cover"
                />
              </div>

              <div>
                <p className="mb-2 text-[10px] font-medium uppercase tracking-wider text-neutral-500">
                  What ClipContext outputs
                </p>
                <CaptionTabs active={activePool} onChange={setActivePool} size="sm" />
              </div>

              <div className="rounded-lg border border-neutral-200 bg-[#faf9f6] p-4 shadow-sm">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activePool}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
                  >
                    {activePool === "titles" && (
                      <div className="space-y-2">
                        {sampleTitles.map((titleText, index) => (
                          <div
                            key={titleText}
                            className="flex items-center justify-between gap-3 rounded-lg border border-neutral-200 bg-white px-3 py-2.5"
                          >
                            <span className="text-sm font-medium leading-snug text-neutral-950">
                              {titleText}
                            </span>
                            {index === 0 ? (
                              <span className="shrink-0 rounded-full border border-emerald-400/25 bg-emerald-500/10 px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.18em] text-emerald-700">
                                Top Ranked
                              </span>
                            ) : (
                              <span className="shrink-0 rounded-md bg-neutral-100 px-2 py-0.5 text-[10px] font-medium text-neutral-500">
                                #{index + 1}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {activePool === "descriptions" && (
                      <div>
                        <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-neutral-500">
                          Top Ranked Description
                        </p>
                        <p className="text-sm leading-relaxed text-neutral-700">
                          {sampleDescription}
                        </p>
                      </div>
                    )}

                    {activePool === "hashtags" && (
                      <div className="flex flex-wrap gap-2">
                        {sampleHashtags.map((tag) => (
                          <span
                            key={tag}
                            className="rounded-full border border-neutral-200 bg-white px-3 py-1.5 text-xs font-medium text-[#365f53]"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </motion.div>
                </AnimatePresence>
              </div>
            </div>
          </motion.div>

        </motion.div>
      </div>
    </section>
  );
}
