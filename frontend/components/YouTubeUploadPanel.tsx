"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  CheckCircle2,
  ExternalLink,
  Loader2,
  PlugZap,
  Youtube,
} from "lucide-react";
import {
  YouTubeApiError,
  createYouTubeUpload,
  disconnectYouTube,
  getYouTubeConnectUrl,
  getYouTubeStatus,
} from "@/lib/api";
import { useYouTubeUploadPolling } from "@/lib/useYouTubeUploadPolling";
import type {
  YouTubeConnectionStatus,
  YouTubePrivacyStatus,
} from "@/types/youtube";

interface YouTubeUploadPanelProps {
  jobId: string | null;
  jobComplete: boolean;
  title: string;
  description: string;
  hashtags: string[];
}

const ERROR_COPY: Record<string, { message: string; actionLabel?: string }> = {
  YOUTUBE_NOT_CONNECTED: {
    message: "Connect your YouTube account to continue.",
    actionLabel: "Connect YouTube",
  },
  YOUTUBE_RECONNECT_REQUIRED: {
    message: "Your YouTube connection has expired.",
    actionLabel: "Reconnect YouTube",
  },
  YOUTUBE_NO_CHANNEL: {
    message:
      "No YouTube channel is available for this Google account. Use a Google account that has a YouTube channel.",
  },
  YOUTUBE_QUOTA_EXCEEDED: {
    message: "YouTube's API quota is currently exhausted. Please try again later.",
  },
  YOUTUBE_API_DISABLED: {
    message: "YouTube Data API access is not enabled for this app yet.",
  },
  YOUTUBE_INSUFFICIENT_SCOPE: {
    message: "ClipContext isn't authorized to upload to this account.",
    actionLabel: "Reconnect YouTube",
  },
  YOUTUBE_UPLOAD_FAILED: {
    message: "The upload to YouTube failed. Please try again.",
  },
  YOUTUBE_UPLOAD_IN_PROGRESS: {
    message: "An upload for this video is already in progress.",
  },
  YOUTUBE_OAUTH_NOT_CONFIGURED: {
    message: "YouTube connection isn't configured on this server yet.",
  },
  OAUTH_STATE_INVALID: {
    message: "Your YouTube sign-in attempt expired. Please try connecting again.",
  },
  OAUTH_DENIED: {
    message: "YouTube authorization was cancelled.",
  },
  OAUTH_EXCHANGE_FAILED: {
    message: "Something went wrong connecting your YouTube account. Please try again.",
  },
  VIDEO_SOURCE_MISSING: {
    message: "The original ClipContext video is no longer available on the server.",
  },
  JOB_NOT_FOUND: {
    message: "This ClipContext job could not be found.",
  },
  JOB_INCOMPLETE: {
    message: "ClipContext is still processing this video.",
  },
};

function copyForCode(code: string | null | undefined, fallback: string) {
  if (!code) return { message: fallback, actionLabel: undefined as string | undefined };
  return ERROR_COPY[code] ?? { message: fallback, actionLabel: undefined };
}

export default function YouTubeUploadPanel({
  jobId,
  jobComplete,
  title,
  description,
  hashtags,
}: YouTubeUploadPanelProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [statusLoading, setStatusLoading] = useState(true);
  const [connection, setConnection] = useState<YouTubeConnectionStatus | null>(null);
  const [callbackNotice, setCallbackNotice] = useState<{
    message: string;
    actionLabel?: string;
  } | null>(null);

  const [privacyStatus, setPrivacyStatus] = useState<YouTubePrivacyStatus>("private");
  const [madeForKids, setMadeForKids] = useState<boolean | null>(null);
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);

  const [uploadId, setUploadId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<{
    message: string;
    actionLabel?: string;
  } | null>(null);

  const { uploadStatus, error: pollError } = useYouTubeUploadPolling(uploadId);

  const refreshStatus = useCallback(async () => {
    try {
      const data = await getYouTubeStatus();
      setConnection(data);
    } catch {
      setConnection({
        connected: false,
        channel_id: null,
        channel_title: null,
        channel_thumbnail_url: null,
      });
    } finally {
      setStatusLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  // OAuth redirects land back on /results?youtube=connected|error&code=...
  // Consume it once, then strip it from the URL — it's a one-time signal,
  // never a token.
  useEffect(() => {
    const youtubeParam = searchParams.get("youtube");
    if (!youtubeParam) return;

    if (youtubeParam === "connected") {
      refreshStatus();
    } else if (youtubeParam === "error") {
      const code = searchParams.get("code");
      setCallbackNotice(copyForCode(code, "Connecting your YouTube account failed."));
    }

    const params = new URLSearchParams(searchParams.toString());
    params.delete("youtube");
    params.delete("code");
    const query = params.toString();
    router.replace(query ? `/results?${query}` : "/results", { scroll: false });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const handleDisconnect = useCallback(async () => {
    try {
      await disconnectYouTube();
    } finally {
      setConnection({
        connected: false,
        channel_id: null,
        channel_title: null,
        channel_thumbnail_url: null,
      });
      setUploadId(null);
      setCreateError(null);
      setAwaitingConfirmation(false);
    }
  }, []);

  const changePrivacyStatus = useCallback((value: YouTubePrivacyStatus) => {
    setPrivacyStatus(value);
    setAwaitingConfirmation(false);
  }, []);

  const changeMadeForKids = useCallback((value: boolean) => {
    setMadeForKids(value);
    setAwaitingConfirmation(false);
  }, []);

  const trimmedTitle = title.trim();
  const trimmedDescription = description.trim();
  const hasHashtags = hashtags.length > 0;
  const isUploadActive = uploadStatus
    ? uploadStatus.status === "queued" || uploadStatus.status === "uploading"
    : Boolean(uploadId) && !uploadStatus;

  const canUpload =
    Boolean(connection?.connected) &&
    jobComplete &&
    Boolean(trimmedTitle) &&
    Boolean(trimmedDescription) &&
    hasHashtags &&
    madeForKids !== null &&
    Boolean(jobId) &&
    !creating &&
    !isUploadActive &&
    uploadStatus?.status !== "completed";

  // Clicking "Upload to YouTube" never fires the request directly — it only
  // opens a final confirmation step showing exactly what's about to be
  // published. Only the "Confirm & Upload" action in that step actually
  // calls the API.
  const handleRequestUpload = useCallback(() => {
    if (!canUpload) return;
    setAwaitingConfirmation(true);
  }, [canUpload]);

  const handleCancelConfirmation = useCallback(() => {
    setAwaitingConfirmation(false);
  }, []);

  const handleConfirmUpload = useCallback(async () => {
    if (!jobId || !canUpload || madeForKids === null) return;

    setAwaitingConfirmation(false);
    setCreating(true);
    setCreateError(null);

    try {
      const created = await createYouTubeUpload(jobId, {
        title: trimmedTitle,
        description: trimmedDescription,
        hashtags,
        privacy_status: privacyStatus,
        made_for_kids: madeForKids,
      });
      setUploadId(created.upload_id);
    } catch (err) {
      if (err instanceof YouTubeApiError) {
        setCreateError(copyForCode(err.code, err.message));
      } else {
        setCreateError({ message: "Failed to start the YouTube upload." });
      }
    } finally {
      setCreating(false);
    }
  }, [jobId, canUpload, madeForKids, trimmedTitle, trimmedDescription, hashtags, privacyStatus]);

  const handleRetry = useCallback(() => {
    setUploadId(null);
    setCreateError(null);
    setAwaitingConfirmation(false);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      className="rounded-lg border border-neutral-200 bg-white/70 p-6 shadow-sm backdrop-blur-xl"
    >
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-neutral-950">YouTube</p>
          <p className="text-sm text-neutral-600">
            Upload the original video to your channel.
          </p>
        </div>
        <div className="rounded-full border border-red-500/20 bg-red-500/10 p-2 text-red-500">
          <Youtube size={16} />
        </div>
      </div>

      {callbackNotice && (
        <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {callbackNotice.message}
        </div>
      )}

      {statusLoading ? (
        <div className="flex items-center gap-2 text-sm text-neutral-500">
          <Loader2 size={16} className="animate-spin" />
          Checking YouTube connection…
        </div>
      ) : connection?.connected ? (
        <div className="space-y-5">
          <div className="flex items-center justify-between rounded-lg border border-neutral-200 bg-[#faf9f6] px-3 py-3">
            <div className="flex items-center gap-3">
              {connection.channel_thumbnail_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={connection.channel_thumbnail_url}
                  alt=""
                  className="h-9 w-9 rounded-full border border-neutral-200 object-cover"
                />
              ) : (
                <div className="flex h-9 w-9 items-center justify-center rounded-full border border-neutral-200 bg-white text-sm font-semibold text-neutral-700">
                  {(connection.channel_title ?? "Y").charAt(0)}
                </div>
              )}
              <div>
                <p className="text-sm font-medium text-neutral-950">
                  {connection.channel_title ?? "YouTube channel"}
                </p>
                <p className="text-xs text-emerald-600">YouTube Connected</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 size={15} className="text-emerald-500" />
              <button
                type="button"
                onClick={handleDisconnect}
                className="rounded-full border border-neutral-300 bg-white px-3 py-1.5 text-xs font-semibold text-neutral-700 transition-colors hover:border-red-300 hover:text-red-600"
              >
                Disconnect
              </button>
            </div>
          </div>

          {uploadStatus?.status === "completed" ? (
            <UploadSuccessCard
              videoTitle={uploadStatus.title ?? trimmedTitle}
              videoUrl={uploadStatus.video_url}
              channelTitle={connection.channel_title}
              privacyStatus={privacyStatus}
            />
          ) : (
            <ReviewAndUploadForm
              jobComplete={jobComplete}
              title={trimmedTitle}
              description={trimmedDescription}
              hashtags={hashtags}
              channelTitle={connection.channel_title}
              privacyStatus={privacyStatus}
              onPrivacyChange={changePrivacyStatus}
              madeForKids={madeForKids}
              onMadeForKidsChange={changeMadeForKids}
              canUpload={canUpload}
              isUploadActive={isUploadActive}
              awaitingConfirmation={awaitingConfirmation}
              onRequestUpload={handleRequestUpload}
              onCancelConfirmation={handleCancelConfirmation}
              onConfirmUpload={handleConfirmUpload}
              uploadStatus={uploadStatus}
              createError={createError}
              pollError={pollError}
              onRetry={handleRetry}
              onReconnect={handleDisconnect}
            />
          )}
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-neutral-600">
            Connect your YouTube account to publish this video directly to
            your channel once you&apos;ve chosen a title, description, and
            hashtags.
          </p>
          <a
            href={getYouTubeConnectUrl()}
            className="inline-flex items-center gap-2 rounded-full bg-neutral-950 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:bg-red-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f5f2]"
          >
            <PlugZap size={16} />
            Connect YouTube
          </a>
        </div>
      )}
    </motion.div>
  );
}

function ReviewAndUploadForm({
  jobComplete,
  title,
  description,
  hashtags,
  channelTitle,
  privacyStatus,
  onPrivacyChange,
  madeForKids,
  onMadeForKidsChange,
  canUpload,
  isUploadActive,
  awaitingConfirmation,
  onRequestUpload,
  onCancelConfirmation,
  onConfirmUpload,
  uploadStatus,
  createError,
  pollError,
  onRetry,
  onReconnect,
}: {
  jobComplete: boolean;
  title: string;
  description: string;
  hashtags: string[];
  channelTitle: string | null;
  privacyStatus: YouTubePrivacyStatus;
  onPrivacyChange: (value: YouTubePrivacyStatus) => void;
  madeForKids: boolean | null;
  onMadeForKidsChange: (value: boolean) => void;
  canUpload: boolean;
  isUploadActive: boolean;
  awaitingConfirmation: boolean;
  onRequestUpload: () => void;
  onCancelConfirmation: () => void;
  onConfirmUpload: () => void;
  uploadStatus: ReturnType<typeof useYouTubeUploadPolling>["uploadStatus"];
  createError: { message: string; actionLabel?: string } | null;
  pollError: ReturnType<typeof useYouTubeUploadPolling>["error"];
  onRetry: () => void;
  onReconnect: () => void;
}) {
  const failureCopy =
    uploadStatus?.status === "failed"
      ? copyForCode(uploadStatus.code, uploadStatus.error ?? "The upload failed.")
      : pollError
        ? copyForCode(pollError.code, pollError.message)
        : createError;

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-neutral-200 bg-[#faf9f6] p-4">
        <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-neutral-500">
          Upload review
        </p>
        <p className="text-sm font-medium text-neutral-900">{title || "No title selected"}</p>
        <p className="mt-1 line-clamp-3 text-xs text-neutral-600">
          {description || "No description selected"}
        </p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {hashtags.map((tag) => (
            <span
              key={tag}
              className="rounded-full border border-neutral-200 bg-white px-2 py-0.5 text-[10px] font-medium text-[#365f53]"
            >
              {tag}
            </span>
          ))}
        </div>
        {channelTitle && (
          <p className="mt-2 text-[10px] text-neutral-500">To: {channelTitle}</p>
        )}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className="mb-1.5 block text-[10px] font-medium uppercase tracking-wider text-neutral-500">
            Privacy
          </label>
          <select
            value={privacyStatus}
            onChange={(event) => onPrivacyChange(event.target.value as YouTubePrivacyStatus)}
            disabled={isUploadActive}
            className="w-full rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 disabled:opacity-60"
          >
            <option value="private">Private</option>
            <option value="unlisted">Unlisted</option>
            <option value="public">Public</option>
          </select>
        </div>

        <div>
          <label className="mb-1.5 block text-[10px] font-medium uppercase tracking-wider text-neutral-500">
            Audience
          </label>
          <select
            value={madeForKids === null ? "" : madeForKids ? "yes" : "no"}
            onChange={(event) => onMadeForKidsChange(event.target.value === "yes")}
            disabled={isUploadActive}
            className="w-full rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 disabled:opacity-60"
          >
            <option value="" disabled>
              Choose an option
            </option>
            <option value="no">No, it&apos;s not made for kids</option>
            <option value="yes">Yes, it&apos;s made for kids</option>
          </select>
        </div>
      </div>

      {!jobComplete && (
        <p className="text-xs text-amber-600">
          Waiting for ClipContext processing to finish before you can upload.
        </p>
      )}

      {isUploadActive && uploadStatus && (
        <div className="space-y-2">
          <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-200">
            <motion.div
              className="h-full rounded-full bg-red-500"
              initial={{ width: 0 }}
              animate={{ width: `${uploadStatus.progress}%` }}
              transition={{ ease: "easeOut", duration: 0.3 }}
            />
          </div>
          <p className="flex items-center gap-2 text-xs text-neutral-600">
            <Loader2 size={12} className="animate-spin" />
            {uploadStatus.message ?? "Uploading…"} ({uploadStatus.progress}%)
          </p>
        </div>
      )}

      {failureCopy && (
        <div className="space-y-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <p>{failureCopy.message}</p>
          {failureCopy.actionLabel === "Reconnect YouTube" ? (
            <button
              type="button"
              onClick={onReconnect}
              className="rounded-full bg-red-600 px-3 py-1.5 text-xs font-semibold text-white"
            >
              Reconnect YouTube
            </button>
          ) : (
            <button
              type="button"
              onClick={onRetry}
              className="rounded-full border border-red-300 bg-white px-3 py-1.5 text-xs font-semibold text-red-700"
            >
              Try again
            </button>
          )}
        </div>
      )}

      {awaitingConfirmation && !isUploadActive ? (
        <div className="space-y-3 rounded-lg border border-neutral-300 bg-neutral-50 p-4">
          <p className="text-sm font-semibold text-neutral-900">Confirm upload</p>
          <p className="text-xs text-neutral-600">
            This publishes the video to <strong>{channelTitle ?? "your YouTube channel"}</strong>{" "}
            as <strong>{privacyStatus}</strong>, marked{" "}
            <strong>{madeForKids ? "made for kids" : "not made for kids"}</strong>. This action
            cannot be undone from ClipContext.
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onCancelConfirmation}
              className="flex-1 rounded-full border border-neutral-300 bg-white px-4 py-2 text-sm font-semibold text-neutral-700 transition-colors hover:border-neutral-400"
            >
              Cancel
            </button>
            <motion.button
              type="button"
              whileHover={{ y: -1, scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              onClick={onConfirmUpload}
              className="flex flex-1 items-center justify-center gap-2 rounded-full bg-neutral-950 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:bg-red-600"
            >
              <Youtube size={16} />
              Confirm &amp; Upload
            </motion.button>
          </div>
        </div>
      ) : (
        <motion.button
          type="button"
          whileHover={canUpload ? { y: -1, scale: 1.01 } : undefined}
          whileTap={canUpload ? { scale: 0.98 } : undefined}
          onClick={onRequestUpload}
          disabled={!canUpload}
          className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-neutral-950 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:bg-red-600 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isUploadActive ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Uploading…
            </>
          ) : (
            <>
              <Youtube size={16} />
              Upload to YouTube
            </>
          )}
        </motion.button>
      )}
    </div>
  );
}

function UploadSuccessCard({
  videoTitle,
  videoUrl,
  channelTitle,
  privacyStatus,
}: {
  videoTitle: string;
  videoUrl: string | null;
  channelTitle: string | null;
  privacyStatus: YouTubePrivacyStatus;
}) {
  return (
    <div className="space-y-3 rounded-lg border border-emerald-200 bg-emerald-50 p-4">
      <div className="flex items-center gap-2 text-emerald-700">
        <CheckCircle2 size={18} />
        <p className="text-sm font-semibold">Uploaded to YouTube</p>
      </div>
      <p className="text-sm text-neutral-800">{videoTitle}</p>
      <p className="text-xs text-neutral-600">
        {privacyStatus.charAt(0).toUpperCase() + privacyStatus.slice(1)}
        {channelTitle ? ` · ${channelTitle}` : ""}
      </p>
      {videoUrl && (
        <a
          href={videoUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-full bg-neutral-950 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-red-600"
        >
          <ExternalLink size={14} />
          View on YouTube
        </a>
      )}
    </div>
  );
}
