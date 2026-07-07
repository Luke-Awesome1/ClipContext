"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, ChevronDown, FileVideo, Upload } from "lucide-react";
import { useVideoSession } from "@/context/VideoSessionContext";
import SectionReveal from "@/components/ui/SectionReveal";

const ACCEPTED = ["video/mp4", "video/quicktime", "video/webm"];
const ACCEPTED_EXT = "MP4, MOV, WEBM";

export default function UploadSection() {
  const router = useRouter();
  const { setVideo, creatorContext, updateCreatorContext } = useVideoSession();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [creatorContextOpen, setCreatorContextOpen] = useState(false);
  const [isInputFocused, setIsInputFocused] = useState(false);
  const [validationMessage, setValidationMessage] = useState<string | null>(null);

  const isValidYouTubeUrl = useMemo(() => {
    if (!creatorContext.youtubeChannelUrl.trim()) return true;
    const value = creatorContext.youtubeChannelUrl.trim();
    const normalized = value.startsWith("http") ? value : `https://${value}`;
    const youtubePattern = /^(https?:\/\/)?(www\.)?(youtube\.com|m\.youtube\.com)\/(?:@[^/]+|channel\/[^/?#]+|c\/[^/?#]+|user\/[^/?#]+)(?:[/?#].*)?$/i;
    return youtubePattern.test(normalized);
  }, [creatorContext.youtubeChannelUrl]);

  const handleChannelUrlChange = useCallback(
    (value: string) => {
      updateCreatorContext({ youtubeChannelUrl: value });
      if (!value.trim()) {
        setValidationMessage(null);
        return;
      }

      const normalized = value.trim();
      const candidate = normalized.startsWith("http") ? normalized : `https://${normalized}`;
      const youtubePattern = /^(https?:\/\/)?(www\.)?(youtube\.com|m\.youtube\.com)\/(?:@[^/]+|channel\/[^/?#]+|c\/[^/?#]+|user\/[^/?#]+)(?:[/?#].*)?$/i;
      const valid = youtubePattern.test(candidate);
      setValidationMessage(valid ? null : "Please enter a valid YouTube channel URL, such as https://youtube.com/@creator.");
    },
    [updateCreatorContext],
  );

  const validateAndSelect = useCallback((file: File) => {
    const validType =
      ACCEPTED.includes(file.type) ||
      Boolean(file.name.match(/\.(mp4|mov|webm)$/i));

    if (!validType) {
      setError("Please upload an MP4, MOV, or WEBM file.");
      return false;
    }

    setError(null);
    setFileName(file.name);
    setSelectedFile(file);
    return true;
  }, []);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files?.length) return;
      validateAndSelect(files[0]);
    },
    [validateAndSelect],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles],
  );

  const startProcessing = useCallback(() => {
    if (!selectedFile) return;
    setVideo(selectedFile);
    router.push("/process");
  }, [selectedFile, setVideo, router]);

  return (
    <section id="upload" className="relative py-24 sm:py-32">
      <div id="demo" className="absolute -top-20" aria-hidden />

      <div className="mx-auto max-w-3xl px-5 sm:px-8">
        <SectionReveal delay={0.04} className="mb-10 text-center">
          <p className="mb-3 text-sm font-medium uppercase tracking-[0.24em] text-blue-400">
            Get Started
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            Upload your video
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-base text-neutral-400">
            Drop a clip between 30 seconds and 2 minutes. Lumina handles the
            rest.
          </p>
        </SectionReveal>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-40px" }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragEnter={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={(e) => {
            if (e.currentTarget.contains(e.relatedTarget as Node | null)) return;
            setDragging(false);
          }}
          onDrop={onDrop}
          className={`group relative cursor-pointer rounded-[1.75rem] border border-dashed p-10 transition-all duration-300 sm:p-14 ${
            dragging
              ? "border-blue-400/60 bg-blue-500/[0.08] shadow-[0_0_70px_rgba(91,140,255,0.2)]"
              : "border-white/[0.12] bg-white/[0.02] hover:border-blue-400/40 hover:bg-white/[0.04] hover:shadow-[0_0_48px_rgba(91,140,255,0.12)]"
          }`}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              inputRef.current?.click();
            }
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".mp4,.mov,.webm,video/mp4,video/quicktime,video/webm"
            className="hidden"
            onChange={(e) => handleFiles(e.target.files)}
          />

          <div className="pointer-events-none absolute inset-0 rounded-2xl bg-gradient-to-b from-blue-500/0 to-blue-500/0 opacity-0 transition-opacity duration-500 group-hover:from-blue-500/[0.04] group-hover:to-transparent group-hover:opacity-100" />

          <div className="relative flex flex-col items-center text-center">
            <motion.div
              animate={dragging ? { y: [0, -3, 0], scale: [1, 1.02, 1] } : { y: 0, scale: 1 }}
              transition={{ duration: 0.45, ease: "easeInOut" }}
              className={`mb-6 flex h-16 w-16 items-center justify-center rounded-2xl border transition-all duration-300 ${
                dragging
                  ? "border-blue-400/40 bg-blue-500/15 text-blue-300"
                  : "border-white/[0.08] bg-white/[0.04] text-neutral-400 group-hover:border-blue-400/30 group-hover:text-blue-400"
              }`}
            >
              <Upload size={28} strokeWidth={1.5} />
            </motion.div>

            <p className="text-lg font-medium text-white">
              {fileName ? fileName : "Drag and drop your video here"}
            </p>
            <p className="mt-2 text-sm text-neutral-500">
              or click to browse from your device
            </p>

            <motion.button
              type="button"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={(e) => {
                e.stopPropagation();
                inputRef.current?.click();
              }}
              className="mt-8 inline-flex items-center gap-2 rounded-full border border-white/[0.1] bg-white/[0.06] px-5 py-2.5 text-sm font-semibold text-white backdrop-blur-sm transition-all duration-300 hover:border-blue-400/30 hover:bg-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/70 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0C0F0F]"
            >
              <FileVideo size={16} />
              Browse Files
            </motion.button>

            <div className="mt-10 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-neutral-500">
              <span className="flex items-center gap-1.5">
                <span className="h-1 w-1 rounded-full bg-neutral-600" />
                MP4
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-1 w-1 rounded-full bg-neutral-600" />
                MOV
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-1 w-1 rounded-full bg-neutral-600" />
                WEBM
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-1 w-1 rounded-full bg-blue-500/60" />
                30 sec – 2 min
              </span>
            </div>
          </div>
        </motion.div>

        <AnimatePresence>
          {error && (
            <motion.p
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-3 text-center text-sm text-red-400/90"
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {selectedFile && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              className="mt-6 space-y-4"
            >
              <motion.button
                type="button"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={startProcessing}
                className="mx-auto flex items-center gap-2 rounded-full bg-blue-500 px-8 py-3.5 text-sm font-semibold text-white shadow-[0_0_32px_rgba(91,140,255,0.24)] transition-all duration-300 hover:-translate-y-0.5 hover:bg-blue-400 hover:shadow-[0_0_42px_rgba(91,140,255,0.32)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/70 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0C0F0F]"
              >
                Analyze with Lumina
                <ArrowRight size={16} />
              </motion.button>

              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="mx-auto w-full max-w-2xl overflow-hidden rounded-[1.35rem] border border-white/[0.08] bg-white/[0.03] shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] backdrop-blur-xl"
              >
                <button
                  type="button"
                  onClick={() => setCreatorContextOpen((v) => !v)}
                  className="flex w-full items-center justify-between px-5 py-4 text-left text-sm font-medium text-white transition-colors hover:bg-white/[0.04] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/70 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0C0F0F]"
                >
                  <span className="flex items-center gap-2">
                    <span className="text-base text-blue-300">✦</span>
                    <span>
                      <span className="block">Creator Context (Optional)</span>
                      <span className="mt-0.5 block text-xs font-normal text-neutral-400">
                        Personalize your results using your existing content
                      </span>
                    </span>
                  </span>
                  <motion.span
                    animate={{ rotate: creatorContextOpen ? 180 : 0 }}
                    transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
                  >
                    <ChevronDown size={16} className="text-neutral-400" />
                  </motion.span>
                </button>

                <AnimatePresence initial={false}>
                  {creatorContextOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
                      className="overflow-hidden"
                    >
                      <div className="border-t border-white/[0.06] px-5 py-4">
                        <label className="mb-2 block text-sm font-medium text-neutral-200" htmlFor="channel-url">
                          YouTube Channel URL
                        </label>
                        <motion.div
                          animate={{
                            boxShadow: isInputFocused
                              ? "0 0 0 1px rgba(96, 165, 250, 0.35), 0 0 30px rgba(59, 130, 246, 0.12)"
                              : "0 0 0 1px rgba(255,255,255,0.04)",
                            y: isInputFocused ? -1 : 0,
                            scale: isInputFocused ? 1.005 : 1,
                          }}
                          transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
                          className="rounded-2xl border border-white/[0.08] bg-black/20 backdrop-blur-sm"
                        >
                          <input
                            id="channel-url"
                            type="url"
                            value={creatorContext.youtubeChannelUrl}
                            onChange={(e) => handleChannelUrlChange(e.target.value)}
                            onFocus={() => setIsInputFocused(true)}
                            onBlur={() => setIsInputFocused(false)}
                            placeholder="https://youtube.com/@creator"
                            className="w-full rounded-2xl bg-transparent px-3 py-3 text-sm text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] placeholder:text-neutral-500 focus-visible:outline-none"
                          />
                        </motion.div>

                        <AnimatePresence mode="wait">
                          {validationMessage ? (
                            <motion.p
                              key="validation"
                              initial={{ opacity: 0, y: -4 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: -4 }}
                              className="mt-2 text-sm text-amber-300/90"
                            >
                              {validationMessage}
                            </motion.p>
                          ) : (
                            <motion.p
                              key="helper"
                              initial={{ opacity: 0, y: -4 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: -4 }}
                              className="mt-3 text-sm leading-6 text-neutral-400"
                            >
                              Allow Lumina AI to analyze your previous 50 YouTube uploads to understand your writing style, tone, structure and publishing patterns. This helps generate titles, descriptions and hashtags that feel more authentic to your content.
                            </motion.p>
                          )}
                        </AnimatePresence>

                        <label className="mt-4 flex cursor-pointer items-start gap-3 rounded-2xl border border-white/[0.06] bg-white/[0.03] px-3 py-3 transition-all duration-200 hover:border-blue-400/20 hover:bg-white/[0.04]">
                          <motion.input
                            type="checkbox"
                            checked={creatorContext.useCreatorContext}
                            onChange={(e) => updateCreatorContext({ useCreatorContext: e.target.checked })}
                            whileTap={{ scale: 0.95 }}
                            className="mt-0.5 h-4 w-4 rounded border-white/20 bg-transparent accent-emerald-400"
                          />
                          <span className="flex-1">
                            <span className="block text-sm font-medium text-white">
                              Analyze my previous uploads to personalize results
                            </span>
                            <span className="mt-1 block text-sm leading-6 text-neutral-400">
                              This is completely optional. If left empty, Lumina AI will still generate results using only your uploaded video and current niche trends.
                            </span>
                          </span>
                        </label>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        <p className="mt-4 text-center text-xs text-neutral-600">
          Supported formats: {ACCEPTED_EXT}
        </p>
      </div>
    </section>
  );
}
