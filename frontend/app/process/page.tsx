"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import StudioNavbar from "@/components/StudioNavbar";
import JourneyStepper from "@/components/JourneyStepper";
import ProcessingPanel from "@/components/ProcessingPanel";
import VideoPreview from "@/components/VideoPreview";
import { useVideoSession } from "@/context/VideoSessionContext";
import { PIPELINE_STAGES } from "@/lib/generatedContent";
import PageTransition from "@/components/ui/PageTransition";

export default function ProcessPage() {
  const router = useRouter();
  const { hasSession, videoUrl, fileName, isDemo } = useVideoSession();
  const [activeStageIndex, setActiveStageIndex] = useState(0);
  const [stageProgress, setStageProgress] = useState(0);

  useEffect(() => {
    if (!hasSession) {
      router.replace("/#upload");
    }
  }, [hasSession, router]);

  useEffect(() => {
    if (!hasSession) return;

    let stageIndex = 0;
    let progress = 0;
    let raf: number;
    let lastTime = performance.now();

    const tick = (now: number) => {
      const delta = now - lastTime;
      lastTime = now;
      const stage = PIPELINE_STAGES[stageIndex];
      if (!stage) return;

      const increment = (delta / stage.durationMs) * 100;
      progress = Math.min(100, progress + increment);
      setStageProgress(progress);
      setActiveStageIndex(stageIndex);

      if (progress >= 100) {
        stageIndex += 1;
        progress = 0;
        if (stageIndex >= PIPELINE_STAGES.length) {
          router.push("/results");
          return;
        }
      }

      raf = requestAnimationFrame(tick);
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [hasSession, router]);

  if (!hasSession) return null;

  return (
    <PageTransition>
      <main className="min-h-screen bg-[#0C0F0F] pt-24 pb-20 text-white">
        <StudioNavbar />

        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute left-1/2 top-0 h-[480px] w-[640px] -translate-x-1/2 rounded-full bg-blue-600/8 blur-[120px]" />
        </div>

        <div className="relative mx-auto max-w-6xl px-5 sm:px-8">
          <JourneyStepper current="processing" />

          <div className="grid items-start gap-12 lg:grid-cols-2">
            <ProcessingPanel
              activeStageIndex={activeStageIndex}
              stageProgress={stageProgress}
            />

            <div className="hidden lg:block">
              <div className="sticky top-28 rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4 backdrop-blur-xl">
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
