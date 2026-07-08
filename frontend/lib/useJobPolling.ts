"use client";

import { useEffect, useRef, useState } from "react";
import { getJob } from "@/lib/api";
import type { JobStatusResponse } from "@/types/video";

const POLL_INTERVAL_MS = 1500;

interface UseJobPollingResult {
  jobStatus: JobStatusResponse | null;
  error: string | null;
}

export function useJobPolling(jobId: string | null): UseJobPollingResult {
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (!jobId) {
      setJobStatus(null);
      setError(null);
      return;
    }

    const controller = new AbortController();
    let timeoutId: ReturnType<typeof setTimeout> | undefined;
    let stopped = false;

    async function poll() {
      try {
        const data = await getJob(jobId as string, controller.signal);

        if (!mountedRef.current || stopped) return;

        setJobStatus(data);
        setError(null);

        if (data.status === "completed" || data.status === "failed") {
          stopped = true;
          return;
        }

        timeoutId = setTimeout(poll, POLL_INTERVAL_MS);
      } catch (err) {
        if (!mountedRef.current || stopped) return;
        if (err instanceof DOMException && err.name === "AbortError") return;

        setError(
          err instanceof Error ? err.message : "Failed to reach ClipContext API",
        );
        timeoutId = setTimeout(poll, POLL_INTERVAL_MS);
      }
    }

    poll();

    return () => {
      stopped = true;
      controller.abort();
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [jobId]);

  return { jobStatus, error };
}
