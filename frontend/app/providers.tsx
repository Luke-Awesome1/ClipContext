"use client";

import { AuthProvider } from "@/context/AuthContext";
import { VideoSessionProvider } from "@/context/VideoSessionContext";

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <VideoSessionProvider>{children}</VideoSessionProvider>
    </AuthProvider>
  );
}
