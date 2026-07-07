"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { CreatorContext } from "@/types/video";

type WorkspaceMode = "guest" | "workspace";

interface VideoSessionContextValue {
  videoUrl: string | null;
  fileName: string | null;
  isDemo: boolean;
  hasSession: boolean;
  isAuthenticated: boolean;
  workspaceMode: WorkspaceMode;
  creatorContext: CreatorContext;
  setVideo: (file: File) => void;
  startDemo: () => void;
  clearSession: () => void;
  continueWithoutWorkspace: () => void;
  createFreeWorkspace: () => void;
  updateCreatorContext: (updates: Partial<CreatorContext>) => void;
  clearCreatorContext: () => void;
}

const VideoSessionContext = createContext<VideoSessionContextValue | null>(null);

export function VideoSessionProvider({ children }: { children: React.ReactNode }) {
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [isDemo, setIsDemo] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [workspaceMode, setWorkspaceMode] = useState<WorkspaceMode>("guest");
  const [creatorContext, setCreatorContext] = useState<CreatorContext>({
    youtubeChannelUrl: "",
    useCreatorContext: false,
  });

  useEffect(() => {
    return () => {
      if (videoUrl) URL.revokeObjectURL(videoUrl);
    };
  }, [videoUrl]);

  const setVideo = useCallback((file: File) => {
    setVideoUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return URL.createObjectURL(file);
    });
    setFileName(file.name);
    setIsDemo(false);
  }, []);

  const startDemo = useCallback(() => {
    setVideoUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    setFileName("product-demo.mp4");
    setIsDemo(true);
  }, []);

  const clearSession = useCallback(() => {
    setVideoUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    setFileName(null);
    setIsDemo(false);
  }, []);

  const continueWithoutWorkspace = useCallback(() => {
    setIsAuthenticated(false);
    setWorkspaceMode("guest");
  }, []);

  const createFreeWorkspace = useCallback(() => {
    setIsAuthenticated(true);
    setWorkspaceMode("workspace");
  }, []);

  const updateCreatorContext = useCallback((updates: Partial<CreatorContext>) => {
    setCreatorContext((prev) => ({ ...prev, ...updates }));
  }, []);

  const clearCreatorContext = useCallback(() => {
    setCreatorContext({ youtubeChannelUrl: "", useCreatorContext: false });
  }, []);

  const value = useMemo(
    () => ({
      videoUrl,
      fileName,
      isDemo,
      hasSession: Boolean(videoUrl || isDemo),
      isAuthenticated,
      workspaceMode,
      creatorContext,
      setVideo,
      startDemo,
      clearSession,
      continueWithoutWorkspace,
      createFreeWorkspace,
      updateCreatorContext,
      clearCreatorContext,
    }),
    [videoUrl, fileName, isDemo, isAuthenticated, workspaceMode, creatorContext, setVideo, startDemo, clearSession, continueWithoutWorkspace, createFreeWorkspace, updateCreatorContext, clearCreatorContext],
  );

  return (
    <VideoSessionContext.Provider value={value}>
      {children}
    </VideoSessionContext.Provider>
  );
}

export function useVideoSession() {
  const ctx = useContext(VideoSessionContext);
  if (!ctx) {
    throw new Error("useVideoSession must be used within VideoSessionProvider");
  }
  return ctx;
}
