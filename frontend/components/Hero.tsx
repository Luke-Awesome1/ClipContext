"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowRight, Play, Sparkles } from "lucide-react";
import { useVideoSession } from "@/context/VideoSessionContext";

const captionStyles = ["Professional", "Sarcastic", "Tech Humour", "Relatable"] as const;

const stylePreviews: Record<
  (typeof captionStyles)[number],
  { title: string; caption: string }
> = {
  Professional: {
    title: "The Dream You Hold Is Still Possible",
    caption:
      "A grounded motivational description built from transcript, visible text, emotional arc, and selected visual windows.",
  },
  Sarcastic: {
    title: "Your Dream Called. It Still Has Audacity.",
    caption:
      "Disappointment arrived loudly. The video still makes the case that the dream deserves another round.",
  },
  "Tech Humour": {
    title: "POV: the dream is still possible",
    caption:
      "city window, visible dream text, mountain shot, full main character recovery arc.",
  },
  Relatable: {
    title: "The Dream Is Running Late, Not Cancelled",
    caption: "A short-form caption that keeps the motivational point clear without inventing details.",
  },
};

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
  const [activeStyle, setActiveStyle] =
    useState<(typeof captionStyles)[number]>("Professional");
  const preview = stylePreviews[activeStyle];

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
            Sparse multimodal analysis for creators
          </motion.div>

          <motion.h1
            custom={1}
            variants={fadeUp}
            className="text-4xl font-semibold leading-[0.98] text-neutral-950 sm:text-5xl lg:text-[3.45rem]"
          >
            Extract the useful context.
            <br />
            <span className="text-[#365f53]">
              Generate grounded candidates.
            </span>
          </motion.h1>

          <motion.p
            custom={2}
            variants={fadeUp}
            className="mt-6 max-w-xl text-base leading-7 text-neutral-600 sm:text-lg"
          >
            ClipContext validates a short video, transcribes speech locally,
            selects sparse temporal frames, builds a canonical VideoContext,
            then generates title, description, and hashtag candidates that stay
            tied to the evidence.
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
              <div className="relative overflow-hidden rounded-lg border border-neutral-200 bg-neutral-900 shadow-sm">
                <div className="aspect-video bg-[linear-gradient(135deg,#1f2933,#111827_45%,#2f3d36)]">
                  <div className="absolute inset-x-0 bottom-0 h-20 bg-black/35" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <motion.div
                      animate={{ y: [0, -3, 0], scale: [1, 1.02, 1] }}
                      transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }}
                      className="flex h-14 w-14 items-center justify-center rounded-full border border-white/20 bg-white/10 backdrop-blur-md"
                    >
                      <Play size={22} className="ml-1 fill-white text-white" />
                    </motion.div>
                  </div>
                  <div className="absolute bottom-3 left-3 rounded-md bg-black/50 px-2 py-1 text-[10px] font-medium text-neutral-300 backdrop-blur-sm">
                    test-video.mp4 · 0:38
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {captionStyles.map((style) => (
                  <button
                    key={style}
                    type="button"
                    onClick={() => setActiveStyle(style)}
                    aria-pressed={activeStyle === style}
                    className={`rounded-full px-3 py-1.5 text-xs font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-white ${
                      activeStyle === style
                        ? "bg-[#365f53]/10 text-[#365f53] ring-1 ring-[#365f53]/25"
                        : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200 hover:text-neutral-950"
                    }`}
                  >
                    {style}
                  </button>
                ))}
              </div>

              <div className="space-y-3 rounded-lg border border-neutral-200 bg-[#faf9f6] p-4 shadow-sm">
                <div>
                  <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-neutral-500">
                    Generated Title Candidate
                  </p>
                  <p className="text-sm font-semibold leading-snug text-neutral-950">
                    {preview.title}
                  </p>
                </div>
                <div className="h-px bg-neutral-200" />
                <div>
                  <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-neutral-500">
                    Description Preview
                  </p>
                  <p className="text-sm leading-relaxed text-neutral-600">
                    {preview.caption}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>

        </motion.div>
      </div>
    </section>
  );
}
