export type YouTubePrivacyStatus = "private" | "unlisted" | "public";

export type YouTubeUploadState = "queued" | "uploading" | "completed" | "failed";

export type YouTubeErrorCode =
  | "YOUTUBE_NOT_CONNECTED"
  | "YOUTUBE_RECONNECT_REQUIRED"
  | "YOUTUBE_NO_CHANNEL"
  | "YOUTUBE_QUOTA_EXCEEDED"
  | "YOUTUBE_API_DISABLED"
  | "YOUTUBE_INSUFFICIENT_SCOPE"
  | "YOUTUBE_UPLOAD_FAILED"
  | "YOUTUBE_UPLOAD_IN_PROGRESS"
  | "YOUTUBE_OAUTH_NOT_CONFIGURED"
  | "OAUTH_STATE_INVALID"
  | "OAUTH_DENIED"
  | "OAUTH_EXCHANGE_FAILED"
  | "VIDEO_SOURCE_MISSING"
  | "JOB_NOT_FOUND"
  | "JOB_INCOMPLETE"
  | "UPLOAD_NOT_FOUND";

export interface YouTubeConnectionStatus {
  connected: boolean;
  channel_id: string | null;
  channel_title: string | null;
  channel_thumbnail_url: string | null;
}

export interface YouTubeUploadRequest {
  title: string;
  description: string;
  hashtags: string[];
  privacy_status: YouTubePrivacyStatus;
  made_for_kids: boolean;
}

export interface YouTubeUploadCreated {
  upload_id: string;
  status: string;
}

export interface YouTubeUploadStatus {
  upload_id: string;
  status: YouTubeUploadState;
  progress: number;
  message: string | null;
  video_id: string | null;
  video_url: string | null;
  title: string | null;
  code: YouTubeErrorCode | null;
  error: string | null;
}

export interface YouTubeApiErrorDetail {
  code: YouTubeErrorCode | string;
  message: string;
}
