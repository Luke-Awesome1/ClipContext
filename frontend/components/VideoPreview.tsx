"use client";

import { Play } from "lucide-react";

interface VideoPreviewProps {
  videoUrl: string | null;
  fileName: string | null;
  isDemo?: boolean;
  className?: string;
}

export default function VideoPreview({
  videoUrl,
  fileName,
  isDemo = false,
  className = "",
}: VideoPreviewProps) {
  return (
    <div
      className={`relative overflow-hidden rounded-xl border border-white/[0.08] bg-neutral-900/80 ${className}`}
    >
      {videoUrl ? (
        <video
          src={videoUrl}
          controls
          className="aspect-video w-full bg-black object-contain"
          playsInline
        />
      ) : (
        <div className="relative aspect-video bg-gradient-to-br from-neutral-800 via-neutral-900 to-[#0C0F0F]">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_30%_20%,rgba(59,130,246,0.18),transparent_55%)]" />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-full border border-white/20 bg-white/10 backdrop-blur-md">
              <Play size={22} className="ml-1 fill-white text-white" />
            </div>
          </div>
        </div>
      )}
      {fileName && (
        <div className="absolute bottom-3 left-3 rounded-md bg-black/50 px-2 py-1 text-[10px] font-medium text-neutral-300 backdrop-blur-sm">
          {fileName}
          {isDemo ? " · demo" : ""}
        </div>
      )}
    </div>
  );
}
