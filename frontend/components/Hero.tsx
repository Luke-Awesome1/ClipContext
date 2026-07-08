"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowRight, Play, Sparkles } from "lucide-react";
import { useVideoSession } from "@/context/VideoSessionContext";

const captionStyles = ["Professional", "Casual", "Creative", "Minimal"] as const;

const stylePreviews: Record<
  (typeof captionStyles)[number],
  { title: string; caption: string }
> = {
  Professional: {
    title: "Scaling Product-Led Growth in 2026",
    caption:
      "In this segment, the speaker outlines three frameworks for sustainable PLG — from onboarding velocity to expansion revenue loops.",
  },
  Casual: {
    title: "okay so here's the thing about growth 👀",
    caption:
      "real talk — most teams overcomplicate PLG. start with one killer onboarding moment and build from there.",
  },
  Creative: {
    title: "When Growth Becomes Gravity ✦",
    caption:
      "Every product has a moment where users stop searching — and start orbiting. This is how you find yours.",
  },
  Minimal: {
    title: "Product-led growth",
    caption: "Three frameworks. One onboarding moment. Sustainable expansion.",
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
        <div className="absolute left-1/2 top-0 h-[520px] w-[720px] -translate-x-1/2 rounded-full bg-blue-500/10 blur-[140px]" />
        <div className="absolute -right-20 top-28 h-72 w-72 rounded-full bg-slate-400/10 blur-[110px]" />
        <div className="absolute bottom-0 left-0 h-56 w-56 rounded-full bg-white/5 blur-[100px]" />
      </div>

      <div className="relative mx-auto grid max-w-6xl items-center gap-16 px-5 sm:px-8 lg:grid-cols-2 lg:gap-12">
        <motion.div initial="hidden" animate="visible" className="max-w-xl">
          <motion.div
            custom={0}
            variants={fadeUp}
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-xs font-medium text-neutral-300 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] backdrop-blur-sm"
          >
            <Sparkles size={14} className="text-blue-400" />
            Multimodal AI for thoughtful creators
          </motion.div>

          <motion.h1
            custom={1}
            variants={fadeUp}
            className="text-4xl font-semibold leading-[0.96] tracking-[-0.03em] text-white sm:text-5xl lg:text-[3.45rem]"
          >
            Understand Every Video.
            <br />
            <span className="bg-gradient-to-r from-white via-neutral-200 to-neutral-400 bg-clip-text text-transparent">
              Create Better Content.
            </span>
          </motion.h1>

          <motion.p
            custom={2}
            variants={fadeUp}
            className="mt-6 max-w-xl text-base leading-7 text-neutral-400 sm:text-lg"
          >
            ClipContext listens to speech and reads visuals — analyzing scenes,
            on-screen text, and tone together — to generate captions, titles,
            and hooks that actually match your video.
          </motion.p>

          <motion.div
            custom={3}
            variants={fadeUp}
            className="mt-10 flex flex-wrap items-center gap-4"
          >
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Link
                href="#upload"
                className="inline-flex items-center gap-2 rounded-full bg-blue-500 px-6 py-3 text-sm font-semibold text-white shadow-[0_0_32px_rgba(91,140,255,0.24)] transition-all duration-300 hover:-translate-y-0.5 hover:bg-blue-400 hover:shadow-[0_0_42px_rgba(91,140,255,0.35)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/70 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0C0F0F]"
              >
                Upload Video
                <ArrowRight size={16} />
              </Link>
            </motion.div>
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <button
                type="button"
                onClick={handleWatchDemo}
                className="inline-flex items-center gap-2 rounded-full border border-white/[0.1] bg-white/[0.04] px-6 py-3 text-sm font-semibold text-white backdrop-blur-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-white/20 hover:bg-white/[0.07] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/70 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0C0F0F]"
              >
                <Play size={16} className="fill-white text-white" />
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
            className="relative rounded-[1.75rem] border border-white/[0.1] bg-white/[0.05] p-4 shadow-[0_30px_90px_rgba(0,0,0,0.38)] backdrop-blur-2xl sm:p-5"
          >
            <div className="absolute -inset-px rounded-[1.75rem] bg-gradient-to-b from-white/[0.14] via-white/[0.06] to-transparent opacity-60" />

            <div className="relative space-y-4">
              <div className="relative overflow-hidden rounded-[1.15rem] border border-white/[0.06] bg-neutral-900/80 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
                <div className="aspect-video bg-gradient-to-br from-neutral-800 via-neutral-900 to-[#0C0F0F]">
                  <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_30%_20%,rgba(91,140,255,0.18),transparent_55%)]" />
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
                    product-demo.mp4 · 1:24
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
                    className={`rounded-full px-3 py-1.5 text-xs font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/70 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0C0F0F] ${
                      activeStyle === style
                        ? "bg-blue-500/20 text-blue-300 ring-1 ring-blue-400/30"
                        : "bg-white/[0.04] text-neutral-400 hover:bg-white/[0.07] hover:text-neutral-200"
                    }`}
                  >
                    {style}
                  </button>
                ))}
              </div>

              <div className="space-y-3 rounded-[1.15rem] border border-white/[0.06] bg-black/20 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
                <div>
                  <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-neutral-500">
                    Generated Title
                  </p>
                  <p className="text-sm font-semibold leading-snug text-white">
                    {preview.title}
                  </p>
                </div>
                <div className="h-px bg-white/[0.06]" />
                <div>
                  <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-neutral-500">
                    Caption Preview
                  </p>
                  <p className="text-sm leading-relaxed text-neutral-400">
                    {preview.caption}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>

          <div className="absolute -bottom-6 -left-6 -z-10 h-32 w-32 rounded-full bg-blue-500/20 blur-3xl" />
          <div className="absolute -right-4 -top-4 -z-10 h-24 w-24 rounded-full bg-sky-400/15 blur-2xl" />
        </motion.div>
      </div>
    </section>
  );
}
