"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Check, FolderOpen, Loader2, Save, Sparkles } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { ArtifactApiError, createArtifact } from "@/lib/api";
import AuthPromptModal from "@/components/AuthPromptModal";

interface SaveArtifactPanelProps {
  jobId: string | null;
  videoDisplayName: string | null;
  selectedTitleId: number | null;
  selectedDescriptionId: number | null;
  selectedHashtagId: number | null;
  isDemo: boolean;
}

type SaveState = "idle" | "saving" | "saved" | "error";

export default function SaveArtifactPanel({
  jobId,
  videoDisplayName,
  selectedTitleId,
  selectedDescriptionId,
  selectedHashtagId,
  isDemo,
}: SaveArtifactPanelProps) {
  const { isAuthenticated, getIdToken } = useAuth();
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [savedArtifactId, setSavedArtifactId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [authPromptOpen, setAuthPromptOpen] = useState(false);

  const hasSelection =
    selectedTitleId !== null && selectedDescriptionId !== null && selectedHashtagId !== null;
  const canSave = Boolean(jobId) && hasSelection && !isDemo;

  const performSave = useCallback(async () => {
    if (!jobId || !hasSelection) return;

    setSaveState("saving");
    setErrorMessage(null);

    try {
      const idToken = await getIdToken();

      if (!idToken) {
        setSaveState("error");
        setErrorMessage("Your session expired. Please sign in again.");
        return;
      }

      const artifact = await createArtifact(
        {
          job_id: jobId,
          selected_title_id: selectedTitleId as number,
          selected_description_id: selectedDescriptionId as number,
          selected_hashtag_set_id: selectedHashtagId as number,
          video_display_name: videoDisplayName,
        },
        idToken,
      );

      setSavedArtifactId(artifact.artifact_id);
      setSaveState("saved");
    } catch (err) {
      setSaveState("error");
      setErrorMessage(
        err instanceof ArtifactApiError ? err.message : "Could not save this artifact.",
      );
    }
  }, [
    jobId,
    hasSelection,
    getIdToken,
    selectedTitleId,
    selectedDescriptionId,
    selectedHashtagId,
    videoDisplayName,
  ]);

  const handleSaveClick = useCallback(() => {
    if (!canSave) return;

    if (!isAuthenticated) {
      setAuthPromptOpen(true);
      return;
    }

    performSave();
  }, [canSave, isAuthenticated, performSave]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      className="rounded-lg border border-neutral-200 bg-white/70 p-6 shadow-sm backdrop-blur-xl"
    >
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#365f53]/20 bg-[#365f53]/10 text-[#365f53]">
          <Sparkles size={18} />
        </div>
        <div>
          <p className="text-sm font-semibold text-neutral-950">Save this generation</p>
          <p className="text-sm text-neutral-600">
            Keep the generated titles, descriptions, hashtags, and AI analysis.
          </p>
        </div>
      </div>

      {isDemo && (
        <p className="mb-4 text-xs text-amber-600">
          Demo results can&apos;t be saved — try it with a real upload.
        </p>
      )}

      {errorMessage && saveState === "error" && (
        <p className="mb-4 text-sm text-red-600">{errorMessage}</p>
      )}

      {saveState === "saved" && savedArtifactId ? (
        <div className="flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-2 rounded-full border border-emerald-400/25 bg-emerald-500/10 px-4 py-2.5 text-sm font-semibold text-emerald-700">
            <Check size={16} />
            Saved
          </span>
          <Link
            href="/artifacts"
            className="inline-flex items-center gap-2 rounded-full border border-neutral-300 bg-white px-4 py-2.5 text-sm font-semibold text-neutral-900 transition-all duration-200 hover:-translate-y-0.5 hover:border-[#365f53]/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
          >
            <FolderOpen size={16} />
            My Artifacts
          </Link>
        </div>
      ) : (
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleSaveClick}
            disabled={!canSave || saveState === "saving"}
            className="inline-flex items-center gap-2 rounded-full bg-neutral-950 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#365f53] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#365f53]/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
          >
            {saveState === "saving" ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Saving…
              </>
            ) : (
              <>
                <Save size={16} />
                Save Results
              </>
            )}
          </button>
        </div>
      )}

      <AuthPromptModal
        open={authPromptOpen}
        title="Keep this generation"
        description="Sign in with Google to save your generated titles, descriptions, hashtags, and AI analysis — and revisit them later."
        onClose={() => setAuthPromptOpen(false)}
        onSuccess={performSave}
      />
    </motion.div>
  );
}
