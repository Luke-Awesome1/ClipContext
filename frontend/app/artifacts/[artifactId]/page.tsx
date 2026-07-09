"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowLeft,
  ExternalLink,
  Loader2,
  Sparkles,
  Trash2,
  Youtube,
} from "lucide-react";
import StudioNavbar from "@/components/StudioNavbar";
import AIUnderstandingCard from "@/components/AIUnderstandingCard";
import CaptionTabs, { type CandidatePool } from "@/components/CaptionTabs";
import PageTransition from "@/components/ui/PageTransition";
import { useAuth } from "@/context/AuthContext";
import { ArtifactApiError, deleteArtifact, getArtifact } from "@/lib/api";
import type { SavedArtifact } from "@/types/artifact";
import type { RankedCandidate } from "@/types/video";

function rankOf(rankings: RankedCandidate[], id: number): RankedCandidate | undefined {
  return rankings.find((entry) => entry.id === id);
}

function sortByRank<T extends { id: number }>(candidates: T[], rankings: RankedCandidate[]) {
  return candidates
    .map((candidate) => ({ ...candidate, ...(rankOf(rankings, candidate.id) ?? { rank: candidate.id, score: 0, reason: "" }) }))
    .sort((a, b) => a.rank - b.rank);
}

export default function ArtifactDetailPage() {
  const params = useParams<{ artifactId: string }>();
  const router = useRouter();
  const { loading, isAuthenticated, getIdToken } = useAuth();
  const [artifact, setArtifact] = useState<SavedArtifact | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [activePool, setActivePool] = useState<CandidatePool>("titles");
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (loading || !isAuthenticated) return;

    let cancelled = false;

    (async () => {
      const idToken = await getIdToken();
      if (!idToken) return;

      try {
        const data = await getArtifact(params.artifactId, idToken);
        if (!cancelled) setArtifact(data);
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ArtifactApiError && err.status === 404) {
          setNotFound(true);
        } else {
          setError(err instanceof ArtifactApiError ? err.message : "Could not load this artifact.");
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [loading, isAuthenticated, getIdToken, params.artifactId]);

  const rankedTitles = useMemo(
    () => (artifact ? sortByRank(artifact.generated_content.titles, artifact.rankings.titles) : []),
    [artifact],
  );
  const rankedDescriptions = useMemo(
    () =>
      artifact
        ? sortByRank(artifact.generated_content.descriptions, artifact.rankings.descriptions)
        : [],
    [artifact],
  );
  const rankedHashtags = useMemo(
    () =>
      artifact ? sortByRank(artifact.generated_content.hashtags, artifact.rankings.hashtags) : [],
    [artifact],
  );

  const handleDelete = useCallback(async () => {
    if (!artifact) return;
    setDeleting(true);
    try {
      const idToken = await getIdToken();
      if (!idToken) return;
      await deleteArtifact(artifact.artifact_id, idToken);
      router.push("/artifacts");
    } catch (err) {
      setError(err instanceof ArtifactApiError ? err.message : "Could not delete this artifact.");
      setDeleting(false);
    }
  }, [artifact, getIdToken, router]);

  return (
    <PageTransition>
      <main className="min-h-screen bg-[#f6f5f2] pt-24 pb-20 text-neutral-950">
        <StudioNavbar />

        <div className="relative mx-auto max-w-4xl px-5 sm:px-8">
          <Link
            href="/artifacts"
            className="mb-6 inline-flex items-center gap-2 text-sm font-medium text-neutral-600 transition-colors hover:text-neutral-950"
          >
            <ArrowLeft size={14} />
            My Artifacts
          </Link>

          {!loading && !isAuthenticated && (
            <div className="rounded-lg border border-neutral-200 bg-white/70 p-10 text-center text-sm text-neutral-600">
              Sign in to view this artifact.
            </div>
          )}

          {isAuthenticated && notFound && (
            <div className="flex flex-col items-center gap-2 rounded-lg border border-neutral-200 bg-white/70 p-10 text-center">
              <AlertTriangle size={22} className="text-neutral-400" />
              <p className="text-sm text-neutral-600">
                This artifact doesn&apos;t exist or isn&apos;t yours.
              </p>
            </div>
          )}

          {isAuthenticated && error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <AlertTriangle size={16} />
              {error}
            </div>
          )}

          {isAuthenticated && !artifact && !notFound && !error && (
            <div className="flex items-center gap-2 text-sm text-neutral-500">
              <Loader2 size={16} className="animate-spin" />
              Loading artifact…
            </div>
          )}

          {isAuthenticated && artifact && (
            <div className="space-y-6">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="mb-2 text-sm font-medium uppercase tracking-widest text-[#365f53]">
                    Saved Artifact
                  </p>
                  <h1 className="text-2xl font-semibold tracking-tight text-neutral-950 sm:text-3xl">
                    {artifact.video.display_name || artifact.video_context.topic}
                  </h1>
                  <p className="mt-2 text-sm text-neutral-500">
                    Saved {new Date(artifact.created_at).toLocaleString()}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleDelete}
                  disabled={deleting}
                  className="inline-flex items-center gap-2 rounded-full border border-neutral-300 bg-white px-4 py-2.5 text-sm font-semibold text-neutral-700 transition-colors hover:border-red-300 hover:text-red-600 disabled:opacity-50"
                >
                  {deleting ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
                  Delete
                </button>
              </div>

              <AIUnderstandingCard videoContext={artifact.video_context} />

              {artifact.youtube_upload.uploaded && (
                <div className="flex flex-wrap items-center gap-3 rounded-lg border border-neutral-200 bg-white/70 p-5 shadow-sm backdrop-blur-xl">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full border border-red-500/20 bg-red-500/10 text-red-500">
                    <Youtube size={18} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-neutral-950">Uploaded to YouTube</p>
                    <p className="text-xs text-neutral-500">
                      {artifact.youtube_upload.privacy_status ?? "private"}
                      {artifact.youtube_upload.channel_title
                        ? ` · ${artifact.youtube_upload.channel_title}`
                        : ""}
                    </p>
                  </div>
                  {artifact.youtube_upload.video_url && (
                    <a
                      href={artifact.youtube_upload.video_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 rounded-full bg-neutral-950 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-red-600"
                    >
                      <ExternalLink size={14} />
                      View on YouTube
                    </a>
                  )}
                </div>
              )}

              <div className="rounded-lg border border-neutral-200 bg-white/70 p-5 shadow-sm backdrop-blur-xl sm:p-6">
                <div className="mb-5">
                  <p className="mb-3 text-xs font-medium uppercase tracking-wider text-neutral-500">
                    Candidate Pool
                  </p>
                  <CaptionTabs active={activePool} onChange={setActivePool} />
                </div>

                <div className="space-y-2">
                  {activePool === "titles" &&
                    rankedTitles.map((candidate) => (
                      <ArtifactCandidateRow
                        key={candidate.id}
                        label={candidate.text}
                        rank={candidate.rank}
                        score={candidate.score}
                        reason={candidate.reason}
                        isSelected={candidate.id === artifact.selection.title_id}
                      />
                    ))}
                  {activePool === "descriptions" &&
                    rankedDescriptions.map((candidate) => (
                      <ArtifactCandidateRow
                        key={candidate.id}
                        label={candidate.text}
                        rank={candidate.rank}
                        score={candidate.score}
                        reason={candidate.reason}
                        isSelected={candidate.id === artifact.selection.description_id}
                      />
                    ))}
                  {activePool === "hashtags" &&
                    rankedHashtags.map((candidate) => (
                      <ArtifactCandidateRow
                        key={candidate.id}
                        label={candidate.tags.join(" ")}
                        rank={candidate.rank}
                        score={candidate.score}
                        reason={candidate.reason}
                        isSelected={candidate.id === artifact.selection.hashtag_set_id}
                      />
                    ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </PageTransition>
  );
}

function ArtifactCandidateRow({
  label,
  rank,
  score,
  reason,
  isSelected,
}: {
  label: string;
  rank: number;
  score: number;
  reason: string;
  isSelected: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex flex-col gap-1.5 rounded-2xl border px-3 py-3 ${
        isSelected
          ? "border-[#365f53]/40 bg-[#365f53]/10 ring-1 ring-[#365f53]/25"
          : "border-neutral-200 bg-white"
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <span className={`text-sm font-medium ${isSelected ? "text-neutral-950" : "text-neutral-700"}`}>
          {label}
        </span>
        <span className="flex shrink-0 items-center gap-2">
          {isSelected && (
            <span className="inline-flex items-center gap-1 rounded-full border border-[#365f53]/25 bg-[#365f53]/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-[#365f53]">
              <Sparkles size={10} />
              Selected
            </span>
          )}
          <span className="rounded-md bg-neutral-100 px-2 py-0.5 text-[10px] font-medium text-neutral-600">
            #{rank} · {score}
          </span>
        </span>
      </div>
      {reason && <p className="text-xs text-neutral-500">{reason}</p>}
    </motion.div>
  );
}
