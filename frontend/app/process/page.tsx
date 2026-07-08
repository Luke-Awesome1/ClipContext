"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import StudioNavbar from "@/components/StudioNavbar";
import JourneyStepper from "@/components/JourneyStepper";
import ProcessingPanel from "@/components/ProcessingPanel";
import VideoPreview from "@/components/VideoPreview";
import { useVideoSession } from "@/context/VideoSessionContext";
import { useJobPolling } from "@/lib/useJobPolling";
import PageTransition from "@/components/ui/PageTransition";

export default function ProcessPage() {
  const router = useRouter();
  const { hasSession, videoUrl, fileName, isDemo, jobId, setJobStatus } =
    useVideoSession();
  const { jobStatus, error } = useJobPolling(jobId);

  useEffect(() => {
    if (!hasSession) {
      router.replace("/#upload");
    }
  }, [hasSession, router]);

  useEffect(() => {
    if (!jobStatus) return;

    setJobStatus(jobStatus.status);

    if (jobStatus.status === "completed") {
      router.push("/results");
    }
  }, [jobStatus, setJobStatus, router]);

  if (!hasSession) return null;

  // Demo mode has no backend job — keep the legacy staged animation dormant
  // and simply route straight through once mounted.
  if (isDemo && !jobId) {
    return (
      <PageTransition>
        <main className="min-h-screen bg-[#f6f5f2] pt-24 pb-20 text-neutral-950">
          <StudioNavbar />
          <div className="relative mx-auto max-w-6xl px-5 sm:px-8">
            <JourneyStepper current="processing" />
            <ProcessingPanel
              currentStage="completed"
              progress={100}
              message="Demo mode: showing sample output."
              error={null}
            />
          </div>
        </main>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <main className="min-h-screen bg-[#f6f5f2] pt-24 pb-20 text-neutral-950">
        <StudioNavbar />

        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute left-1/2 top-0 h-[360px] w-[560px] -translate-x-1/2 bg-white/45 blur-[120px]" />
        </div>

        <div className="relative mx-auto max-w-6xl px-5 sm:px-8">
          <JourneyStepper current="processing" />

          <div className="grid items-start gap-12 lg:grid-cols-2">
            <ProcessingPanel
              currentStage={jobStatus?.stage ?? "queued"}
              progress={jobStatus?.progress ?? 0}
              message={jobStatus?.message ?? "Connecting to ClipContext..."}
              error={jobStatus?.status === "failed" ? jobStatus.error : error}
            />

            <div className="hidden lg:block">
              <div className="sticky top-28 rounded-lg border border-neutral-200 bg-white/70 p-4 shadow-sm backdrop-blur-xl">
                <p className="mb-3 text-xs font-medium uppercase tracking-wider text-neutral-500">
                  Source Video
                </p>
                <VideoPreview
                  videoUrl={videoUrl}
                  fileName={fileName}
                  isDemo={isDemo}
                />
              </div>
            </div>
          </div>
        </div>
      </main>
    </PageTransition>
  );
}
