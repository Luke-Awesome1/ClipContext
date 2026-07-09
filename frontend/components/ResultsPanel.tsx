"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import type { LucideIcon } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  Copy,
  Download,
  Check,
  Loader2,
  Plus,
  Sparkles,
  X,
} from "lucide-react";
import CaptionTabs, { type CandidatePool } from "@/components/CaptionTabs";
import AIUnderstandingCard from "@/components/AIUnderstandingCard";
import VideoPreview from "@/components/VideoPreview";
import SaveArtifactPanel from "@/components/SaveArtifactPanel";
import YouTubeUploadPanel from "@/components/YouTubeUploadPanel";
import type {
  HashtagCandidate,
  PipelineResult,
  RankedCandidate,
  TextCandidate,
} from "@/types/video";
import SectionReveal from "@/components/ui/SectionReveal";

interface StoredSelection {
  titleId: number;
  descriptionId: number;
  hashtagId: number;
  editedTitle?: string;
  editedDescription?: string;
  editedHashtags?: string[];
}

function selectionStorageKey(jobId: string): string {
  return `clipcontext:selection:${jobId}`;
}

function readStoredSelection(jobId: string): StoredSelection | null {
  if (typeof window === "undefined") return null;

  try {
    const raw = window.sessionStorage.getItem(selectionStorageKey(jobId));
    if (!raw) return null;
    return JSON.parse(raw) as StoredSelection;
  } catch {
    return null;
  }
}

interface ResultsPanelProps {
  videoUrl: string | null;
  fileName: string | null;
  isDemo?: boolean;
  result: PipelineResult | null;
  isLoading: boolean;
  error: string | null;
}

function rankOf(rankings: RankedCandidate[], id: number): RankedCandidate | undefined {
  return rankings.find((entry) => entry.id === id);
}

const TOP_N_CANDIDATES = 5;

function sortByRank<T extends { id: number }>(
  candidates: T[],
  rankings: RankedCandidate[],
): (T & { rank: number; score: number; reason: string })[] {
  return candidates
    .map((candidate) => {
      const ranking = rankOf(rankings, candidate.id);
      return {
        ...candidate,
        rank: ranking?.rank ?? candidate.id,
        score: ranking?.score ?? 0,
        reason: ranking?.reason ?? "",
      };
    })
    .sort((a, b) => a.rank - b.rank)
    .slice(0, TOP_N_CANDIDATES);
}

export default function ResultsPanel({
  videoUrl,
  fileName,
  isDemo = false,
  result,
  isLoading,
  error,
}: ResultsPanelProps) {
  const [activePool, setActivePool] = useState<CandidatePool>("titles");
  const [copied, setCopied] = useState(false);
  const [selectedTitleId, setSelectedTitleId] = useState<number | null>(null);
  const [selectedDescriptionId, setSelectedDescriptionId] = useState<number | null>(null);
  const [selectedHashtagId, setSelectedHashtagId] = useState<number | null>(null);

  // The user can freely edit the selected candidate's text/tags before
  // upload — these hold the editable working copy, seeded from whichever
  // candidate is selected but independent of it once edited.
  const [editedTitle, setEditedTitle] = useState("");
  const [editedDescription, setEditedDescription] = useState("");
  const [editedHashtags, setEditedHashtags] = useState<string[]>([]);

  const rankedTitles = useMemo(
    () => (result ? sortByRank(result.generated_content.titles, result.rankings.titles) : []),
    [result],
  );
  const rankedDescriptions = useMemo(
    () =>
      result
        ? sortByRank(result.generated_content.descriptions, result.rankings.descriptions)
        : [],
    [result],
  );
  const rankedHashtags = useMemo(
    () =>
      result
        ? sortByRank(result.generated_content.hashtags, result.rankings.hashtags)
        : [],
    [result],
  );

  // OAuth for "Connect YouTube" navigates away from this page and back.
  // Selection state is component-local (useState), so without this it would
  // reset to the top-ranked candidates on return — restore whatever the
  // user had picked for this job before persisting the current pick below.
  const storedSelection = result && !isDemo ? readStoredSelection(result.job_id) : null;

  useEffect(() => {
    if (rankedTitles.length && selectedTitleId === null) {
      const stored = storedSelection?.titleId;
      const isValid = stored !== undefined && rankedTitles.some((t) => t.id === stored);
      setSelectedTitleId(isValid ? (stored as number) : rankedTitles[0].id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rankedTitles, selectedTitleId]);

  useEffect(() => {
    if (rankedDescriptions.length && selectedDescriptionId === null) {
      const stored = storedSelection?.descriptionId;
      const isValid = stored !== undefined && rankedDescriptions.some((d) => d.id === stored);
      setSelectedDescriptionId(isValid ? (stored as number) : rankedDescriptions[0].id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rankedDescriptions, selectedDescriptionId]);

  useEffect(() => {
    if (rankedHashtags.length && selectedHashtagId === null) {
      const stored = storedSelection?.hashtagId;
      const isValid = stored !== undefined && rankedHashtags.some((h) => h.id === stored);
      setSelectedHashtagId(isValid ? (stored as number) : rankedHashtags[0].id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rankedHashtags, selectedHashtagId]);

  // Seed the editable working copy from whichever candidate is selected.
  // Switching to a different candidate resets edits to that candidate's
  // text; a restored (post-OAuth-redirect) edit takes priority once, on
  // the render where its id first matches.
  useEffect(() => {
    if (selectedTitleId === null) return;
    const candidate = rankedTitles.find((t) => t.id === selectedTitleId);
    if (!candidate) return;

    const stored = storedSelection;
    setEditedTitle(
      stored && stored.titleId === selectedTitleId && stored.editedTitle !== undefined
        ? stored.editedTitle
        : candidate.text,
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTitleId]);

  useEffect(() => {
    if (selectedDescriptionId === null) return;
    const candidate = rankedDescriptions.find((d) => d.id === selectedDescriptionId);
    if (!candidate) return;

    const stored = storedSelection;
    setEditedDescription(
      stored &&
        stored.descriptionId === selectedDescriptionId &&
        stored.editedDescription !== undefined
        ? stored.editedDescription
        : candidate.text,
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDescriptionId]);

  useEffect(() => {
    if (selectedHashtagId === null) return;
    const candidate = rankedHashtags.find((h) => h.id === selectedHashtagId);
    if (!candidate) return;

    const stored = storedSelection;
    setEditedHashtags(
      stored && stored.hashtagId === selectedHashtagId && stored.editedHashtags !== undefined
        ? stored.editedHashtags
        : [...candidate.tags],
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedHashtagId]);

  useEffect(() => {
    if (
      !result ||
      isDemo ||
      selectedTitleId === null ||
      selectedDescriptionId === null ||
      selectedHashtagId === null
    ) {
      return;
    }

    window.sessionStorage.setItem(
      selectionStorageKey(result.job_id),
      JSON.stringify({
        titleId: selectedTitleId,
        descriptionId: selectedDescriptionId,
        hashtagId: selectedHashtagId,
        editedTitle,
        editedDescription,
        editedHashtags,
      }),
    );
  }, [result, isDemo, selectedTitleId, selectedDescriptionId, selectedHashtagId]);

  const copyAll = useCallback(async () => {
    const text = [
      `Title: ${editedTitle}`,
      "",
      "Description:",
      editedDescription,
      "",
      `Hashtags: ${editedHashtags.join(" ")}`,
    ].join("\n");

    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [editedTitle, editedDescription, editedHashtags]);

  const handleExport = useCallback(() => {
    if (!result) return;

    const payload = {
      fileName: fileName ?? "video",
      jobId: result.job_id,
      generatedAt: new Date().toISOString(),
      selection: {
        title: editedTitle,
        description: editedDescription,
        hashtags: editedHashtags,
      },
      result,
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `clipcontext-${(fileName ?? "export").replace(/\.[^.]+$/, "")}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }, [result, fileName, editedTitle, editedDescription, editedHashtags]);

  if (error) {
    return (
      <div className="mx-auto flex w-full max-w-2xl flex-col items-center gap-4 rounded-lg border border-red-200 bg-red-50 p-10 text-center">
        <AlertTriangle size={28} className="text-red-500" />
        <p className="text-lg font-semibold text-red-700">Processing failed</p>
        <p className="text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (isLoading || !result) {
    return (
      <div className="mx-auto flex w-full max-w-2xl flex-col items-center gap-4 rounded-lg border border-neutral-200 bg-white/70 p-10 text-center">
        <Loader2 size={28} className="animate-spin text-[#365f53]" />
        <p className="text-lg font-semibold text-neutral-950">Fetching results…</p>
        <p className="text-sm text-neutral-600">
          Hang tight, ClipContext is finishing up the last steps.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-6xl">
      <SectionReveal delay={0.04} className="mb-10">
        <p className="mb-3 text-sm font-medium uppercase tracking-widest text-[#365f53]">
          Results
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-neutral-950 sm:text-4xl">
          Candidate sets are ready
        </h1>
        <p className="mt-4 max-w-xl text-base text-neutral-600">
          Compare generated titles, descriptions, and hashtag sets grounded in
          the canonical VideoContext. Titles, descriptions, and hashtags are
          independent candidate pools — pick any combination.
        </p>
      </SectionReveal>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
        <div className="space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="rounded-lg border border-neutral-200 bg-white/70 p-4 shadow-sm backdrop-blur-xl sm:p-5"
          >
            <VideoPreview videoUrl={videoUrl} fileName={fileName} isDemo={isDemo} />
          </motion.div>

          <AIUnderstandingCard videoContext={result.video_context} />
        </div>

        <div className="space-y-5">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.05, ease: [0.16, 1, 0.3, 1] }}
            className="rounded-lg border border-neutral-200 bg-white/70 p-5 shadow-sm backdrop-blur-xl sm:p-6"
          >
            <div className="mb-5">
              <p className="mb-3 text-xs font-medium uppercase tracking-wider text-neutral-500">
                Candidate Pool
              </p>
              <CaptionTabs active={activePool} onChange={setActivePool} />
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                key={activePool}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
                className="space-y-2"
                role="status"
                aria-live="polite"
              >
                {activePool === "titles" &&
                  rankedTitles.map((candidate) => (
                    <CandidateRow
                      key={candidate.id}
                      candidate={candidate}
                      isSelected={candidate.id === selectedTitleId}
                      onSelect={() => setSelectedTitleId(candidate.id)}
                      renderLabel={(c) => c.text}
                    />
                  ))}

                {activePool === "descriptions" &&
                  rankedDescriptions.map((candidate) => (
                    <CandidateRow
                      key={candidate.id}
                      candidate={candidate}
                      isSelected={candidate.id === selectedDescriptionId}
                      onSelect={() => setSelectedDescriptionId(candidate.id)}
                      renderLabel={(c) => c.text}
                    />
                  ))}

                {activePool === "hashtags" &&
                  rankedHashtags.map((candidate) => (
                    <CandidateRow
                      key={candidate.id}
                      candidate={candidate}
                      isSelected={candidate.id === selectedHashtagId}
                      onSelect={() => setSelectedHashtagId(candidate.id)}
                      renderLabel={(c) => c.tags.join(" ")}
                    />
                  ))}
              </motion.div>
            </AnimatePresence>

            <div className="mt-6 space-y-4 border-t border-neutral-200 pt-6">
              <EditableField
                label="Selected Title"
                value={editedTitle}
                onChange={setEditedTitle}
              />
              <EditableField
                label="Selected Description"
                value={editedDescription}
                onChange={setEditedDescription}
                multiline
              />
              <EditableHashtags tags={editedHashtags} onChange={setEditedHashtags} />
            </div>

            <div className="mt-6 flex flex-wrap gap-3 border-t border-neutral-200 pt-6">
              <ActionButton
                icon={copied ? Check : Copy}
                label={copied ? "Copied" : "Copy Selection"}
                onClick={copyAll}
                variant="secondary"
              />
              <ActionButton
                icon={Download}
                label="Export"
                onClick={handleExport}
                variant="primary"
              />
            </div>
          </motion.div>
        </div>
      </div>

      <div className="mt-8 grid gap-6 sm:grid-cols-2">
        <SaveArtifactPanel
          jobId={!isDemo && result ? result.job_id : null}
          videoDisplayName={fileName}
          selectedTitleId={selectedTitleId}
          selectedDescriptionId={selectedDescriptionId}
          selectedHashtagId={selectedHashtagId}
          isDemo={isDemo}
        />
        <Suspense fallback={null}>
          <YouTubeUploadPanel
            jobId={!isDemo && result ? result.job_id : null}
            jobComplete={!isDemo}
            title={editedTitle}
            description={editedDescription}
            hashtags={editedHashtags}
          />
        </Suspense>
      </div>
    </div>
  );
}

function CandidateRow<T extends TextCandidate | HashtagCandidate>({
  candidate,
  isSelected,
  onSelect,
  renderLabel,
}: {
  candidate: T & { rank: number; score: number; reason: string };
  isSelected: boolean;
  onSelect: () => void;
  renderLabel: (candidate: T) => string;
}) {
  const isRecommended = candidate.rank === 1;

  return (
    <motion.button
      type="button"
      onClick={onSelect}
      whileHover={{ x: 2 }}
      whileTap={{ scale: 0.99 }}
      className={`flex w-full flex-col gap-1.5 rounded-2xl border px-3 py-3 text-left transition-all duration-200 ${
        isSelected
          ? "border-[#365f53]/40 bg-[#365f53]/10 ring-1 ring-[#365f53]/25"
          : "border-neutral-300 bg-white hover:border-[#365f53]/20"
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <span className={`text-sm font-medium ${isSelected ? "text-neutral-950" : "text-neutral-700"}`}>
          {renderLabel(candidate)}
        </span>
        <span className="flex shrink-0 items-center gap-2">
          {isRecommended && (
            <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/25 bg-emerald-500/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-700">
              <Sparkles size={10} />
              Top Ranked
            </span>
          )}
          <span className="rounded-md bg-neutral-100 px-2 py-0.5 text-[10px] font-medium text-neutral-600">
            #{candidate.rank} · {candidate.score}
          </span>
        </span>
      </div>
      {candidate.reason && (
        <p className="text-xs text-neutral-500">{candidate.reason}</p>
      )}
    </motion.button>
  );
}

function EditableField({
  label,
  value,
  onChange,
  multiline = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  multiline?: boolean;
}) {
  return (
    <div className="rounded-lg border border-neutral-200 bg-[#faf9f6] p-4 transition-colors focus-within:border-[#365f53]/40 focus-within:bg-white">
      <p className="mb-2 text-[10px] font-medium uppercase tracking-wider text-neutral-500">
        {label}
      </p>
      {multiline ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={3}
          className="w-full resize-none bg-transparent text-sm leading-relaxed text-neutral-800 focus-visible:outline-none"
        />
      ) : (
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-transparent text-sm leading-relaxed text-neutral-800 focus-visible:outline-none"
        />
      )}
    </div>
  );
}

function EditableHashtags({
  tags,
  onChange,
}: {
  tags: string[];
  onChange: (tags: string[]) => void;
}) {
  const [draft, setDraft] = useState("");

  const addTag = () => {
    const cleaned = draft.trim();
    if (!cleaned) return;

    const normalized = cleaned.startsWith("#") ? cleaned : `#${cleaned}`;
    if (tags.some((tag) => tag.toLowerCase() === normalized.toLowerCase())) {
      setDraft("");
      return;
    }

    onChange([...tags, normalized]);
    setDraft("");
  };

  const removeTag = (tag: string) => {
    onChange(tags.filter((t) => t !== tag));
  };

  return (
    <div>
      <p className="mb-2 text-[10px] font-medium uppercase tracking-wider text-neutral-500">
        Selected Hashtags
      </p>
      <div className="flex flex-wrap items-center gap-2">
        {tags.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1.5 rounded-full border border-neutral-200 bg-white px-3 py-1.5 text-xs font-medium text-[#365f53]"
          >
            {tag}
            <button
              type="button"
              onClick={() => removeTag(tag)}
              aria-label={`Remove ${tag}`}
              className="text-neutral-400 transition-colors hover:text-red-500"
            >
              <X size={12} />
            </button>
          </span>
        ))}

        <span className="inline-flex items-center gap-1 rounded-full border border-dashed border-neutral-300 bg-transparent px-2.5 py-1.5">
          <input
            type="text"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addTag();
              }
            }}
            placeholder="Add hashtag"
            className="w-24 bg-transparent text-xs text-neutral-700 placeholder:text-neutral-400 focus-visible:outline-none"
          />
          <button
            type="button"
            onClick={addTag}
            aria-label="Add hashtag"
            className="text-neutral-400 transition-colors hover:text-[#365f53]"
          >
            <Plus size={12} />
          </button>
        </span>
      </div>
    </div>
  );
}

function ActionButton({
  icon: Icon,
  label,
  onClick,
  variant,
  disabled,
}: {
  icon: LucideIcon;
  label: string;
  onClick: () => void;
  variant: "primary" | "secondary";
  disabled?: boolean;
}) {
  const base =
    "inline-flex items-center gap-2 rounded-full px-4 py-2.5 text-sm font-semibold transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]";
  const styles =
    variant === "primary"
      ? "bg-neutral-950 text-white shadow-sm hover:bg-[#365f53]"
      : "border border-neutral-300 bg-white text-neutral-900 shadow-sm hover:border-[#365f53]/30";

  return (
    <motion.button
      type="button"
      whileHover={disabled ? undefined : { y: -1, scale: 1.01 }}
      whileTap={disabled ? undefined : { scale: 0.98 }}
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${styles}`}
    >
      <Icon size={16} />
      {label}
    </motion.button>
  );
}
