"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { CreatorContext, JobStatus } from "@/types/video";

const JOB_ID_KEY = "clipcontext:jobId";
const FILE_NAME_KEY = "clipcontext:fileName";
const CREATOR_CONTEXT_KEY = "clipcontext:creatorContext";

interface VideoSessionContextValue {
  videoUrl: string | null;
  fileName: string | null;
  isDemo: boolean;
  hasSession: boolean;
  hydrated: boolean;
  jobId: string | null;
  jobStatus: JobStatus | null;
  creatorContext: CreatorContext;
  setVideo: (file: File) => void;
  startDemo: () => void;
  clearSession: () => void;
  updateCreatorContext: (updates: Partial<CreatorContext>) => void;
  clearCreatorContext: () => void;
  setJob: (jobId: string, status: JobStatus) => void;
  setJobStatus: (status: JobStatus) => void;
}

const VideoSessionContext = createContext<VideoSessionContextValue | null>(null);

function readSessionStorage(key: string): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(key);
}

export function VideoSessionProvider({ children }: { children: React.ReactNode }) {
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [isDemo, setIsDemo] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatusState] = useState<JobStatus | null>(null);
  const [creatorContext, setCreatorContext] = useState<CreatorContext>({
    youtubeChannelUrl: "",
  });
  const [hydrated, setHydrated] = useState(false);

  // Recover job identity across a page refresh. The browser File object and
  // its object URL cannot survive a reload, but the job_id can, and the
  // backend remains the source of truth for job/result state.
  useEffect(() => {
    const storedJobId = readSessionStorage(JOB_ID_KEY);
    const storedFileName = readSessionStorage(FILE_NAME_KEY);
    const storedCreatorContext = readSessionStorage(CREATOR_CONTEXT_KEY);

    if (storedJobId) setJobId(storedJobId);
    if (storedFileName) setFileName(storedFileName);

    if (storedCreatorContext) {
      try {
        setCreatorContext(JSON.parse(storedCreatorContext));
      } catch {
        // ignore malformed stored value
      }
    }

    setHydrated(true);
  }, []);

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
    window.sessionStorage.setItem(FILE_NAME_KEY, file.name);
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
    setJobId(null);
    setJobStatusState(null);
    window.sessionStorage.removeItem(JOB_ID_KEY);
    window.sessionStorage.removeItem(FILE_NAME_KEY);
  }, []);

  const updateCreatorContext = useCallback((updates: Partial<CreatorContext>) => {
    setCreatorContext((prev) => {
      const next = { ...prev, ...updates };
      window.sessionStorage.setItem(CREATOR_CONTEXT_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const clearCreatorContext = useCallback(() => {
    setCreatorContext({ youtubeChannelUrl: "" });
    window.sessionStorage.removeItem(CREATOR_CONTEXT_KEY);
  }, []);

  const setJob = useCallback((newJobId: string, status: JobStatus) => {
    setJobId(newJobId);
    setJobStatusState(status);
    window.sessionStorage.setItem(JOB_ID_KEY, newJobId);
  }, []);

  const setJobStatus = useCallback((status: JobStatus) => {
    setJobStatusState(status);
  }, []);

  const value = useMemo(
    () => ({
      videoUrl,
      fileName,
      isDemo,
      hasSession: hydrated && Boolean(videoUrl || isDemo || jobId),
      hydrated,
      jobId,
      jobStatus,
      creatorContext,
      setVideo,
      startDemo,
      clearSession,
      updateCreatorContext,
      clearCreatorContext,
      setJob,
      setJobStatus,
    }),
    [
      videoUrl,
      fileName,
      isDemo,
      hydrated,
      jobId,
      jobStatus,
      creatorContext,
      setVideo,
      startDemo,
      clearSession,
      updateCreatorContext,
      clearCreatorContext,
      setJob,
      setJobStatus,
    ],
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
