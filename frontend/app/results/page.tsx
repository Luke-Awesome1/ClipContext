"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import StudioNavbar from "@/components/StudioNavbar";
import JourneyStepper from "@/components/JourneyStepper";
import ResultsPanel from "@/components/ResultsPanel";
import { useVideoSession } from "@/context/VideoSessionContext";
import PageTransition from "@/components/ui/PageTransition";

export default function ResultsPage() {
  const router = useRouter();
  const { hasSession, videoUrl, fileName, isDemo } = useVideoSession();

  useEffect(() => {
    if (!hasSession) {
      router.replace("/#upload");
    }
  }, [hasSession, router]);

  if (!hasSession) return null;

  return (
    <PageTransition>
      <main className="min-h-screen bg-[#0C0F0F] pt-24 pb-20 text-white">
        <StudioNavbar />

        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute right-0 top-20 h-80 w-80 rounded-full bg-blue-600/8 blur-[100px]" />
        </div>

        <div className="relative mx-auto px-5 sm:px-8">
          <JourneyStepper current="results" />
          <ResultsPanel
            videoUrl={videoUrl}
            fileName={fileName}
            isDemo={isDemo}
          />
        </div>
      </main>
    </PageTransition>
  );
}
