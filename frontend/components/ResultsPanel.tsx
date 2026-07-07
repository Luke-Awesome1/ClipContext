"use client";

import { useCallback, useState } from "react";
import type { LucideIcon } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { Copy, Download, RefreshCw, Check, Sparkles, TrendingUp } from "lucide-react";
import CaptionTabs from "@/components/CaptionTabs";
import AIUnderstandingCard from "@/components/AIUnderstandingCard";
import VideoPreview from "@/components/VideoPreview";
import WorkspacePrompt from "@/components/WorkspacePrompt";
import ConnectedPlatformsPanel from "@/components/ConnectedPlatformsPanel";
import { DEMO_ANALYSIS, buildExportPayload } from "@/lib/generatedContent";
import type { CaptionStyle } from "@/types/video";
import SectionReveal from "@/components/ui/SectionReveal";

interface ResultsPanelProps {
  videoUrl: string | null;
  fileName: string | null;
  isDemo?: boolean;
}

export default function ResultsPanel({
  videoUrl,
  fileName,
  isDemo = false,
}: ResultsPanelProps) {
  const [activeStyle, setActiveStyle] = useState<CaptionStyle>("Formal");
  const [copied, setCopied] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [contentKey, setContentKey] = useState(0);
  const [selectedTitle, setSelectedTitle] = useState(0);

  const output = DEMO_ANALYSIS.outputs[activeStyle];
  const titleOptions = [
    output.title,
    `${output.title} ✦`,
    `${output.title} · Quick Take`,
    `${output.title} · Deep Dive`,
    `How ${output.title.toLowerCase()}`,
  ];

  const copyAll = useCallback(async () => {
    const text = [
      `Title: ${titleOptions[selectedTitle]}`,
      "",
      `Description:`,
      output.caption,
      "",
      `Hashtags: ${output.hashtags.join(" ")}`,
    ].join("\n");

    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [output, selectedTitle, titleOptions]);

  const handleRegenerate = useCallback(() => {
    setRegenerating(true);
    setTimeout(() => {
      setContentKey((k) => k + 1);
      setRegenerating(false);
    }, 1400);
  }, []);

  const handleExport = useCallback(() => {
    const payload = buildExportPayload(activeStyle, fileName);
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `lumina-${(fileName ?? "export").replace(/\.[^.]+$/, "")}-${activeStyle.toLowerCase()}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }, [activeStyle, fileName]);

  return (
    <div className="mx-auto w-full max-w-6xl">
      <SectionReveal delay={0.04} className="mb-10">
        <p className="mb-3 text-sm font-medium uppercase tracking-widest text-blue-400">
          Results
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          Your content is ready
        </h1>
        <p className="mt-4 max-w-xl text-base text-neutral-400">
          Switch caption styles to compare outputs. Every version is grounded in
          what Lumina detected from your video.
        </p>
      </SectionReveal>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
        <div className="space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="rounded-[1.6rem] border border-white/[0.08] bg-white/[0.03] p-4 shadow-[0_24px_90px_rgba(0,0,0,0.22)] backdrop-blur-xl sm:p-5"
          >
            <VideoPreview
              videoUrl={videoUrl}
              fileName={fileName}
              isDemo={isDemo}
            />
          </motion.div>

          <AIUnderstandingCard concepts={DEMO_ANALYSIS.concepts} />
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="rounded-[1.6rem] border border-white/[0.08] bg-white/[0.03] p-6 shadow-[0_24px_90px_rgba(0,0,0,0.22)] backdrop-blur-xl"
          >
            <div className="mb-5 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-blue-400/20 bg-blue-500/10 text-blue-400">
                <TrendingUp size={18} />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">Creator Insights</p>
                <p className="text-sm text-neutral-400">Signals that make the output feel more intentional.</p>
              </div>
            </div>

            <div className="space-y-3">
              {[
                { label: "Detected Niche", value: "Artificial Intelligence" },
                { label: "Creator Style", value: "Educational" },
                { label: "Primary Tone", value: "Professional" },
                { label: "Historical Upload Pattern", value: "Weekly" },
                { label: "Trending Opportunity", value: "AI Agents" },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between rounded-2xl border border-white/[0.06] bg-black/20 px-3 py-3">
                  <span className="text-sm text-neutral-400">{item.label}</span>
                  <span className="text-sm font-medium text-white">{item.value}</span>
                </div>
              ))}
            </div>
          </motion.div>
          <WorkspacePrompt />
        </div>

        <div className="space-y-5">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.05, ease: [0.16, 1, 0.3, 1] }}
            className="rounded-[1.6rem] border border-white/[0.08] bg-white/[0.03] p-5 shadow-[0_24px_90px_rgba(0,0,0,0.22)] backdrop-blur-xl sm:p-6"
          >
            <div className="mb-5">
              <p className="mb-3 text-xs font-medium uppercase tracking-wider text-neutral-500">
                Caption Style
              </p>
              <CaptionTabs active={activeStyle} onChange={setActiveStyle} />
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                key={`${activeStyle}-${contentKey}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: regenerating ? 0.5 : 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
                className="space-y-5"
                role="status"
                aria-live="polite"
              >
                {regenerating ? (
                  <div className="space-y-4" aria-hidden>
                    <div className="h-3 w-2/3 animate-pulse rounded-full bg-white/[0.08]" />
                    <div className="h-3 w-full animate-pulse rounded-full bg-white/[0.08]" />
                    <div className="h-3 w-5/6 animate-pulse rounded-full bg-white/[0.08]" />
                    <div className="h-3 w-3/4 animate-pulse rounded-full bg-white/[0.08]" />
                  </div>
                ) : (
                  <>
                    <div>
                      <p className="mb-3 text-[10px] font-medium uppercase tracking-wider text-neutral-500">
                        Title Recommendations
                      </p>
                      <div className="space-y-2">
                        {titleOptions.map((title, index) => {
                          const isSelected = index === selectedTitle;
                          const isRecommended = index === 0;
                          const rankingClasses = [
                            "border-emerald-400/40 bg-[linear-gradient(135deg,rgba(74,222,128,0.34),rgba(16,185,129,0.24),rgba(3,7,18,0.95))] shadow-[0_0_24px_rgba(74,222,128,0.16)]",
                            "border-emerald-300/30 bg-[linear-gradient(135deg,rgba(74,222,128,0.18),rgba(255,255,255,0.06),rgba(16,185,129,0.10))]",
                            "border-emerald-200/25 bg-[linear-gradient(135deg,rgba(255,255,255,0.08),rgba(167,243,208,0.14),rgba(255,255,255,0.04))]",
                            "border-white/20 bg-[linear-gradient(135deg,rgba(255,255,255,0.10),rgba(187,247,208,0.10),rgba(255,255,255,0.04))]",
                            "border-white/30 bg-white/[0.06]",
                          ];

                          return (
                            <motion.button
                              key={`${title}-${index}`}
                              type="button"
                              onClick={() => setSelectedTitle(index)}
                              whileHover={{ x: 2, scale: 1.01 }}
                              whileTap={{ scale: 0.98 }}
                              className={`flex w-full items-center justify-between rounded-2xl border px-3 py-3 text-left transition-all duration-200 ${
                                isSelected
                                  ? `${rankingClasses[index]} ring-1 ring-blue-400/25`
                                  : `${rankingClasses[index]} hover:border-blue-400/20 hover:bg-white/[0.05]`
                              }`}
                            >
                              <span className={`text-sm font-medium ${isSelected ? "text-white" : "text-neutral-200"}`}>
                                {title}
                              </span>
                              {isRecommended ? (
                                <span className="ml-3 inline-flex items-center gap-1 rounded-full border border-emerald-400/25 bg-emerald-500/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-300">
                                  <Sparkles size={10} />
                                  AI Recommended
                                </span>
                              ) : null}
                            </motion.button>
                          );
                        })}
                      </div>
                    </div>

                    <div className="rounded-[1.2rem] border border-white/[0.06] bg-black/20 p-4">
                      <p className="mb-2 text-[10px] font-medium uppercase tracking-wider text-neutral-500">
                        Selected Title
                      </p>
                      <p className="text-lg font-semibold text-white">{titleOptions[selectedTitle]}</p>
                    </div>

                    <OutputField label="Description" value={output.caption} />
                    <div>
                      <p className="mb-2 text-[10px] font-medium uppercase tracking-wider text-neutral-500">
                        Hashtags
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {output.hashtags.map((tag) => (
                          <motion.button
                            key={tag}
                            type="button"
                            whileHover={{ y: -1, scale: 1.02 }}
                            className="rounded-full border border-white/[0.06] bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-blue-300/90 transition-all duration-200 hover:border-blue-400/20"
                          >
                            #{tag}
                          </motion.button>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </motion.div>
            </AnimatePresence>

            <div className="mt-6 flex flex-wrap gap-3 border-t border-white/[0.06] pt-6">
              <ActionButton
                icon={copied ? Check : Copy}
                label={copied ? "Copied" : "Copy"}
                onClick={copyAll}
                variant="secondary"
              />
              <ActionButton
                icon={RefreshCw}
                label={regenerating ? "Regenerating…" : "Regenerate"}
                onClick={handleRegenerate}
                disabled={regenerating}
                variant="secondary"
                spin={regenerating}
              />
              <ActionButton
                icon={Download}
                label="Export"
                onClick={handleExport}
                variant="primary"
              />
            </div>
          </motion.div>

          <ConnectedPlatformsPanel />
        </div>
      </div>
    </div>
  );
}

function OutputField({
  label,
  value,
  large = false,
}: {
  label: string;
  value: string;
  large?: boolean;
}) {
  return (
    <div>
      <p className="mb-2 text-[10px] font-medium uppercase tracking-wider text-neutral-500">
        {label}
      </p>
      <p
        className={`leading-relaxed text-neutral-300 ${
          large ? "text-lg font-semibold text-white" : "text-sm"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function ActionButton({
  icon: Icon,
  label,
  onClick,
  variant,
  disabled,
  spin,
}: {
  icon: LucideIcon;
  label: string;
  onClick: () => void;
  variant: "primary" | "secondary";
  disabled?: boolean;
  spin?: boolean;
}) {
  const base =
    "inline-flex items-center gap-2 rounded-full px-4 py-2.5 text-sm font-semibold transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/70 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0C0F0F]";
  const styles =
    variant === "primary"
      ? "bg-blue-500 text-white shadow-[0_0_32px_rgba(59,130,246,0.25)] hover:bg-blue-400"
      : "border border-white/[0.1] bg-white/[0.04] text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] hover:border-blue-400/30 hover:bg-blue-500/10";

  return (
    <motion.button
      type="button"
      whileHover={disabled ? undefined : { y: -1, scale: 1.01 }}
      whileTap={disabled ? undefined : { scale: 0.98 }}
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${styles}`}
    >
      <Icon size={16} className={spin ? "animate-spin" : undefined} />
      {label}
    </motion.button>
  );
}
