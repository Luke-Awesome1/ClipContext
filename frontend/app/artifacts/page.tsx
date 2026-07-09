"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { AlertTriangle, ArrowRight, Loader2, Trash2, Youtube } from "lucide-react";
import StudioNavbar from "@/components/StudioNavbar";
import AuthPromptModal from "@/components/AuthPromptModal";
import PageTransition from "@/components/ui/PageTransition";
import { useAuth } from "@/context/AuthContext";
import { ArtifactApiError, deleteArtifact, listArtifacts } from "@/lib/api";
import type { ArtifactSummary } from "@/types/artifact";

export default function ArtifactsPage() {
  const { loading, isAuthenticated, getIdToken } = useAuth();
  const [artifacts, setArtifacts] = useState<ArtifactSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [authPromptOpen, setAuthPromptOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const idToken = await getIdToken();
    if (!idToken) return;

    try {
      const data = await listArtifacts(idToken);
      setArtifacts(data.artifacts);
      setError(null);
    } catch (err) {
      setError(err instanceof ArtifactApiError ? err.message : "Could not load your artifacts.");
    }
  }, [getIdToken]);

  useEffect(() => {
    if (loading || !isAuthenticated) return;
    refresh();
  }, [loading, isAuthenticated, refresh]);

  const handleDelete = useCallback(
    async (artifactId: string) => {
      setDeletingId(artifactId);
      try {
        const idToken = await getIdToken();
        if (!idToken) return;
        await deleteArtifact(artifactId, idToken);
        setArtifacts((prev) => prev?.filter((a) => a.artifact_id !== artifactId) ?? null);
      } catch (err) {
        setError(err instanceof ArtifactApiError ? err.message : "Could not delete this artifact.");
      } finally {
        setDeletingId(null);
      }
    },
    [getIdToken],
  );

  return (
    <PageTransition>
      <main className="min-h-screen bg-[#f6f5f2] pt-24 pb-20 text-neutral-950">
        <StudioNavbar />

        <div className="relative mx-auto max-w-4xl px-5 sm:px-8">
          <div className="mb-10">
            <p className="mb-3 text-sm font-medium uppercase tracking-widest text-[#365f53]">
              My Artifacts
            </p>
            <h1 className="text-3xl font-semibold tracking-tight text-neutral-950 sm:text-4xl">
              Saved generations
            </h1>
            <p className="mt-4 max-w-xl text-base text-neutral-600">
              Titles, descriptions, hashtags, and AI analysis you&apos;ve saved to your account.
            </p>
          </div>

          {loading ? (
            <div className="flex items-center gap-2 text-sm text-neutral-500">
              <Loader2 size={16} className="animate-spin" />
              Loading…
            </div>
          ) : !isAuthenticated ? (
            <div className="flex flex-col items-center gap-4 rounded-lg border border-neutral-200 bg-white/70 p-10 text-center">
              <p className="text-base font-semibold text-neutral-950">Sign in to view your artifacts</p>
              <p className="max-w-sm text-sm text-neutral-600">
                My Artifacts is only available to signed-in ClipContext accounts.
              </p>
              <button
                type="button"
                onClick={() => setAuthPromptOpen(true)}
                className="inline-flex items-center gap-2 rounded-full bg-neutral-950 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:bg-[#365f53]"
              >
                Continue with Google
              </button>
            </div>
          ) : (
            <>
              {error && (
                <div className="mb-4 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  <AlertTriangle size={16} />
                  {error}
                </div>
              )}

              {artifacts === null ? (
                <div className="flex items-center gap-2 text-sm text-neutral-500">
                  <Loader2 size={16} className="animate-spin" />
                  Loading your artifacts…
                </div>
              ) : artifacts.length === 0 ? (
                <div className="rounded-lg border border-neutral-200 bg-white/70 p-10 text-center text-sm text-neutral-600">
                  Nothing saved yet. From any Results page, click{" "}
                  <span className="font-medium text-neutral-900">Save Results</span> to keep a
                  generation here.
                </div>
              ) : (
                <div className="space-y-3">
                  {artifacts.map((artifact, index) => (
                    <motion.div
                      key={artifact.artifact_id}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.03 }}
                      className="flex items-center justify-between gap-4 rounded-lg border border-neutral-200 bg-white/70 p-5 shadow-sm backdrop-blur-xl"
                    >
                      <Link href={`/artifacts/${artifact.artifact_id}`} className="min-w-0 flex-1">
                        <p className="truncate text-sm font-semibold text-neutral-950">
                          {artifact.selected_title || "Untitled generation"}
                        </p>
                        <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-neutral-500">
                          <span>{artifact.topic || artifact.content_type}</span>
                          <span>{new Date(artifact.created_at).toLocaleDateString()}</span>
                          {artifact.youtube_uploaded && (
                            <span className="inline-flex items-center gap-1 text-red-500">
                              <Youtube size={12} />
                              Uploaded
                            </span>
                          )}
                        </p>
                      </Link>

                      <div className="flex shrink-0 items-center gap-2">
                        <Link
                          href={`/artifacts/${artifact.artifact_id}`}
                          className="rounded-full border border-neutral-300 bg-white p-2 text-neutral-600 transition-colors hover:border-[#365f53]/30 hover:text-[#365f53]"
                          aria-label="Open artifact"
                        >
                          <ArrowRight size={14} />
                        </Link>
                        <button
                          type="button"
                          onClick={() => handleDelete(artifact.artifact_id)}
                          disabled={deletingId === artifact.artifact_id}
                          aria-label="Delete artifact"
                          className="rounded-full border border-neutral-300 bg-white p-2 text-neutral-600 transition-colors hover:border-red-300 hover:text-red-600 disabled:opacity-50"
                        >
                          {deletingId === artifact.artifact_id ? (
                            <Loader2 size={14} className="animate-spin" />
                          ) : (
                            <Trash2 size={14} />
                          )}
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        <AuthPromptModal
          open={authPromptOpen}
          title="Log in to ClipContext"
          description="Use Google to continue — this also creates your account on first sign-in."
          onClose={() => setAuthPromptOpen(false)}
        />
      </main>
    </PageTransition>
  );
}
