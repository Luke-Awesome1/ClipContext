"use client";

import { VideoSessionProvider } from "@/context/VideoSessionContext";

export default function Providers({ children }: { children: React.ReactNode }) {
  return <VideoSessionProvider>{children}</VideoSessionProvider>;
}
