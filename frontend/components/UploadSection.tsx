"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, ChevronDown, FileVideo, Upload } from "lucide-react";
import { useVideoSession } from "@/context/VideoSessionContext";
import { createJob, ApiError } from "@/lib/api";
import SectionReveal from "@/components/ui/SectionReveal";

const ACCEPTED = ["video/mp4", "video/quicktime", "video/webm"];
const ACCEPTED_EXT = "MP4, MOV, WEBM";

const YOUTUBE_HANDLE_PATTERN =
  /youtube\.com\/(?:@([^/?#]+)|channel\/([^/?#]+)|c\/([^/?#]+)|user\/([^/?#]+))/i;

function extractCreatorHandle(channelUrl: string): string {
  const trimmed = channelUrl.trim();
  if (!trimmed) return "";
  const match = trimmed.match(YOUTUBE_HANDLE_PATTERN);
  if (!match) return "";
  return match[1] ?? match[2] ?? match[3] ?? match[4] ?? "";
}

export default function UploadSection() {
  const router = useRouter();
  const { setVideo, setJob, creatorContext, updateCreatorContext } =
    useVideoSession();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [creatorContextOpen, setCreatorContextOpen] = useState(false);
  const [isInputFocused, setIsInputFocused] = useState(false);
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

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

  const hasChannelUrl = creatorContext.youtubeChannelUrl.trim().length > 0;

  const startProcessing = useCallback(async () => {
    if (!selectedFile || isSubmitting) return;

    if (hasChannelUrl && !isValidYouTubeUrl) {
      setError("Please enter a valid YouTube channel URL, or clear the field to skip it.");
      return;
    }

    const creatorHandle = hasChannelUrl
      ? extractCreatorHandle(creatorContext.youtubeChannelUrl)
      : "";

    setError(null);
    setIsSubmitting(true);

    try {
      const { job_id: jobId, status } = await createJob({
        video: selectedFile,
        creatorHandle,
        platform: "youtube",
      });

      setVideo(selectedFile);
      setJob(jobId, status);
      router.push("/process");
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Could not reach the ClipContext backend. Is it running?";
      setError(message);
      setIsSubmitting(false);
    }
  }, [
    selectedFile,
    isSubmitting,
    creatorContext,
    hasChannelUrl,
    isValidYouTubeUrl,
    setVideo,
    setJob,
    router,
  ]);

  return (
    <section id="upload" className="relative py-24 sm:py-32">
      <div id="demo" className="absolute -top-20" aria-hidden />

      <div className="mx-auto max-w-3xl px-5 sm:px-8">
        <SectionReveal delay={0.04} className="mb-10 text-center">
          <p className="mb-3 text-sm font-medium uppercase tracking-[0.24em] text-[#365f53]">
            Get Started
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-neutral-950 sm:text-4xl">
            Upload a short clip
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-base text-neutral-600">
            Drop a 30 second to 2 minute video. ClipContext will validate it,
            extract speech, sample sparse frames, and prepare grounded
            publishing candidates.
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
          className={`group relative cursor-pointer rounded-lg border border-dashed p-10 transition-all duration-300 sm:p-14 ${
            dragging
              ? "border-[#365f53]/60 bg-[#365f53]/[0.06] shadow-sm"
              : "border-neutral-300 bg-white/60 hover:border-[#365f53]/35 hover:bg-white"
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

          <div className="relative flex flex-col items-center text-center">
            <motion.div
              animate={dragging ? { y: [0, -3, 0], scale: [1, 1.02, 1] } : { y: 0, scale: 1 }}
              transition={{ duration: 0.45, ease: "easeInOut" }}
              className={`mb-6 flex h-16 w-16 items-center justify-center rounded-2xl border transition-all duration-300 ${
                dragging
                  ? "border-[#365f53]/40 bg-[#365f53]/10 text-[#365f53]"
                  : "border-neutral-200 bg-white text-neutral-500 group-hover:border-[#365f53]/30 group-hover:text-[#365f53]"
              }`}
            >
              <Upload size={28} strokeWidth={1.5} />
            </motion.div>

            <p className="text-lg font-medium text-neutral-950">
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
              className="mt-8 inline-flex items-center gap-2 rounded-full border border-neutral-300 bg-white px-5 py-2.5 text-sm font-semibold text-neutral-900 backdrop-blur-sm transition-all duration-300 hover:border-[#365f53]/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
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
                <span className="h-1 w-1 rounded-full bg-[#365f53]/70" />
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
                whileHover={isSubmitting ? undefined : { scale: 1.02 }}
                whileTap={isSubmitting ? undefined : { scale: 0.98 }}
                onClick={startProcessing}
                disabled={isSubmitting}
                className="mx-auto flex items-center gap-2 rounded-full bg-neutral-950 px-8 py-3.5 text-sm font-semibold text-white shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:bg-[#365f53] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 disabled:hover:bg-neutral-950"
              >
                {isSubmitting ? "Uploading…" : "Analyze with ClipContext"}
                <ArrowRight size={16} />
              </motion.button>

              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="mx-auto w-full max-w-2xl overflow-hidden rounded-lg border border-neutral-200 bg-white/70 shadow-sm backdrop-blur-xl"
              >
                <button
                  type="button"
                  onClick={() => setCreatorContextOpen((v) => !v)}
                  className="flex w-full items-center justify-between px-5 py-4 text-left text-sm font-medium text-neutral-950 transition-colors hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
                >
                  <span className="flex items-center gap-2">
                    <span className="text-base text-[#365f53]">*</span>
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
                      <div className="border-t border-neutral-200 px-5 py-4">
                        <label className="mb-2 block text-sm font-medium text-neutral-800" htmlFor="channel-url">
                          YouTube Channel URL
                        </label>
                        <motion.div
                          animate={{
                            boxShadow: isInputFocused
                              ? "0 0 0 1px rgba(54, 95, 83, 0.35)"
                              : "0 0 0 1px rgba(23,23,23,0.1)",
                            y: isInputFocused ? -1 : 0,
                            scale: isInputFocused ? 1.005 : 1,
                          }}
                          transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
                          className="rounded-lg border border-neutral-200 bg-white backdrop-blur-sm"
                        >
                          <input
                            id="channel-url"
                            type="url"
                            value={creatorContext.youtubeChannelUrl}
                            onChange={(e) => handleChannelUrlChange(e.target.value)}
                            onFocus={() => setIsInputFocused(true)}
                            onBlur={() => setIsInputFocused(false)}
                            placeholder="https://youtube.com/@creator"
                            className="w-full rounded-lg bg-transparent px-3 py-3 text-sm text-neutral-950 placeholder:text-neutral-500 focus-visible:outline-none"
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
                              {hasChannelUrl
                                ? "ClipContext will analyze your previous 50 YouTube uploads to personalize titles, descriptions, and hashtags to your style."
                                : "Optional — paste your channel URL and ClipContext will analyze your previous 50 uploads to personalize results. Leave empty to use only this video and current trends."}
                            </motion.p>
                          )}
                        </AnimatePresence>
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
