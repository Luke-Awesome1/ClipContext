"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import StudioNavbar from "@/components/StudioNavbar";
import JourneyStepper from "@/components/JourneyStepper";
import ResultsPanel from "@/components/ResultsPanel";
import { useVideoSession } from "@/context/VideoSessionContext";
import { useJobPolling } from "@/lib/useJobPolling";
import { DEMO_RESULT } from "@/lib/generatedContent";
import PageTransition from "@/components/ui/PageTransition";

export default function ResultsPage() {
  const router = useRouter();
  const { hasSession, hydrated, videoUrl, fileName, isDemo, jobId } = useVideoSession();
  const { jobStatus, error: pollError } = useJobPolling(isDemo ? null : jobId);

  // Wait for VideoSessionProvider to finish restoring jobId from
  // sessionStorage before deciding there's no session — critical after a
  // full-page redirect (e.g. returning from the YouTube OAuth consent
  // screen), which remounts this whole tree and re-triggers that restore.
  // Redirecting on the pre-hydration "no session yet" render would bounce
  // a user with a perfectly valid in-progress session back to the upload
  // page one tick before their session data actually arrives.
  useEffect(() => {
    if (hydrated && !hasSession) {
      router.replace("/#upload");
    }
  }, [hydrated, hasSession, router]);

  if (!hydrated || !hasSession) return null;

  const result = isDemo ? DEMO_RESULT : (jobStatus?.result ?? null);
  const isLoading = !isDemo && (!jobStatus || jobStatus.status === "processing" || jobStatus.status === "queued");
  const errorMessage = isDemo
    ? null
    : jobStatus?.status === "failed"
      ? (jobStatus.error ?? "Processing failed.")
      : pollError;

  return (
    <PageTransition>
      <main className="min-h-screen bg-[#f6f5f2] pt-24 pb-20 text-neutral-950">
        <StudioNavbar />

        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute right-0 top-20 h-72 w-72 bg-white/45 blur-[100px]" />
        </div>

        <div className="relative mx-auto px-5 sm:px-8">
          <JourneyStepper current="results" />
          <ResultsPanel
            videoUrl={videoUrl}
            fileName={fileName}
            isDemo={isDemo}
            result={result}
            isLoading={isLoading}
            error={errorMessage}
          />
        </div>
      </main>
    </PageTransition>
  );
}
