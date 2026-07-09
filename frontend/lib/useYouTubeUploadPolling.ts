"use client";

import { useEffect, useRef, useState } from "react";
import { getYouTubeUploadStatus, YouTubeApiError } from "@/lib/api";
import type { YouTubeUploadStatus } from "@/types/youtube";

const POLL_INTERVAL_MS = 1500;

interface UseYouTubeUploadPollingResult {
  uploadStatus: YouTubeUploadStatus | null;
  error: YouTubeApiError | null;
}

export function useYouTubeUploadPolling(
  uploadId: string | null,
): UseYouTubeUploadPollingResult {
  const [uploadStatus, setUploadStatus] = useState<YouTubeUploadStatus | null>(null);
  const [error, setError] = useState<YouTubeApiError | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (!uploadId) {
      setUploadStatus(null);
      setError(null);
      return;
    }

    const controller = new AbortController();
    let timeoutId: ReturnType<typeof setTimeout> | undefined;
    let stopped = false;

    async function poll() {
      try {
        const data = await getYouTubeUploadStatus(uploadId as string, controller.signal);

        if (!mountedRef.current || stopped) return;

        setUploadStatus(data);
        setError(null);

        if (data.status === "completed" || data.status === "failed") {
          stopped = true;
          return;
        }

        timeoutId = setTimeout(poll, POLL_INTERVAL_MS);
      } catch (err) {
        if (!mountedRef.current || stopped) return;
        if (err instanceof DOMException && err.name === "AbortError") return;

        if (err instanceof YouTubeApiError) {
          setError(err);
          stopped = true;
          return;
        }

        timeoutId = setTimeout(poll, POLL_INTERVAL_MS);
      }
    }

    poll();

    return () => {
      stopped = true;
      controller.abort();
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [uploadId]);

  return { uploadStatus, error };
}
