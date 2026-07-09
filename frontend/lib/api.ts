import type {
  JobCreateResponse,
  JobStatusResponse,
  Platform,
} from "@/types/video";
import type {
  YouTubeConnectionStatus,
  YouTubeUploadCreated,
  YouTubeUploadRequest,
  YouTubeUploadStatus,
} from "@/types/youtube";
import type {
  ArtifactCreateRequest,
  ArtifactListResponse,
  SavedArtifact,
} from "@/types/artifact";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * Thrown by YouTube endpoints, which return a structured
 * { code, message } detail so the UI can branch on `code` (e.g. show
 * "Reconnect YouTube") instead of parsing prose.
 */
export class YouTubeApiError extends ApiError {
  code: string;

  constructor(message: string, status: number, code: string) {
    super(message, status);
    this.name = "YouTubeApiError";
    this.code = code;
  }
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") return data.detail;
  } catch {
    // response body was not JSON; fall through to generic message
  }
  return `Request failed with status ${response.status}`;
}

async function throwYouTubeError(response: Response): Promise<never> {
  try {
    const data = await response.json();
    const detail = data?.detail;

    if (detail && typeof detail === "object" && typeof detail.code === "string") {
      throw new YouTubeApiError(
        detail.message ?? "YouTube request failed.",
        response.status,
        detail.code,
      );
    }

    if (typeof detail === "string") {
      throw new YouTubeApiError(detail, response.status, "YOUTUBE_UPLOAD_FAILED");
    }
  } catch (err) {
    if (err instanceof YouTubeApiError) throw err;
  }

  throw new YouTubeApiError(
    `Request failed with status ${response.status}`,
    response.status,
    "YOUTUBE_UPLOAD_FAILED",
  );
}

/**
 * Thrown by artifact endpoints (ClipContext account persistence), which
 * return a structured { code, message } detail — distinct from
 * YouTubeApiError since these are two independent auth systems.
 */
export class ArtifactApiError extends ApiError {
  code: string;

  constructor(message: string, status: number, code: string) {
    super(message, status);
    this.name = "ArtifactApiError";
    this.code = code;
  }
}

async function throwArtifactError(response: Response): Promise<never> {
  try {
    const data = await response.json();
    const detail = data?.detail;

    if (detail && typeof detail === "object" && typeof detail.code === "string") {
      throw new ArtifactApiError(
        detail.message ?? "Request failed.",
        response.status,
        detail.code,
      );
    }

    if (typeof detail === "string") {
      throw new ArtifactApiError(detail, response.status, "ARTIFACT_REQUEST_FAILED");
    }
  } catch (err) {
    if (err instanceof ArtifactApiError) throw err;
  }

  throw new ArtifactApiError(
    `Request failed with status ${response.status}`,
    response.status,
    "ARTIFACT_REQUEST_FAILED",
  );
}

export interface CreateJobParams {
  video: File;
  creatorHandle: string;
  platform: Platform;
  signal?: AbortSignal;
}

export async function createJob({
  video,
  creatorHandle,
  platform,
  signal,
}: CreateJobParams): Promise<JobCreateResponse> {
  const formData = new FormData();
  formData.append("video", video);
  formData.append("creator_handle", creatorHandle);
  formData.append("platform", platform);

  const response = await fetch(`${API_BASE_URL}/api/jobs`, {
    method: "POST",
    body: formData,
    signal,
  });

  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status);
  }

  return response.json();
}

export async function getJob(
  jobId: string,
  signal?: AbortSignal,
): Promise<JobStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/jobs/${jobId}`, {
    signal,
  });

  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response), response.status);
  }

  return response.json();
}

export async function checkHealth(signal?: AbortSignal): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, { signal });
    return response.ok;
  } catch {
    return false;
  }
}

// --- YouTube: Connect with YouTube / Upload to YouTube ---
//
// All of these carry the ClipContext session cookie (credentials:
// "include") so the backend can resolve the caller's server-side YouTube
// connection. The cookie itself is HttpOnly — the frontend never reads or
// stores YouTube tokens.

export function getYouTubeConnectUrl(): string {
  return `${API_BASE_URL}/api/youtube/connect`;
}

export async function getYouTubeStatus(
  signal?: AbortSignal,
): Promise<YouTubeConnectionStatus> {
  const response = await fetch(`${API_BASE_URL}/api/youtube/status`, {
    credentials: "include",
    signal,
  });

  if (!response.ok) await throwYouTubeError(response);
  return response.json();
}

export async function disconnectYouTube(
  signal?: AbortSignal,
): Promise<YouTubeConnectionStatus> {
  const response = await fetch(`${API_BASE_URL}/api/youtube/disconnect`, {
    method: "POST",
    credentials: "include",
    signal,
  });

  if (!response.ok) await throwYouTubeError(response);
  return response.json();
}

export async function createYouTubeUpload(
  jobId: string,
  payload: YouTubeUploadRequest,
  signal?: AbortSignal,
): Promise<YouTubeUploadCreated> {
  const response = await fetch(
    `${API_BASE_URL}/api/jobs/${encodeURIComponent(jobId)}/youtube/upload`,
    {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    },
  );

  if (!response.ok) await throwYouTubeError(response);
  return response.json();
}

export async function getYouTubeUploadStatus(
  uploadId: string,
  signal?: AbortSignal,
): Promise<YouTubeUploadStatus> {
  const response = await fetch(
    `${API_BASE_URL}/api/youtube/uploads/${encodeURIComponent(uploadId)}`,
    { credentials: "include", signal },
  );

  if (!response.ok) await throwYouTubeError(response);
  return response.json();
}

// --- ClipContext artifacts (Save Results / My Artifacts) ---
//
// Requires a Firebase ID token, obtained via useAuth().getIdToken() —
// entirely independent of the YouTube session cookie used above. These
// never send credentials: "include"; the Authorization header is the only
// auth channel here.

function authHeaders(idToken: string): HeadersInit {
  return { "Content-Type": "application/json", Authorization: `Bearer ${idToken}` };
}

export async function createArtifact(
  payload: ArtifactCreateRequest,
  idToken: string,
  signal?: AbortSignal,
): Promise<SavedArtifact> {
  const response = await fetch(`${API_BASE_URL}/api/artifacts`, {
    method: "POST",
    headers: authHeaders(idToken),
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) await throwArtifactError(response);
  return response.json();
}

export async function listArtifacts(
  idToken: string,
  signal?: AbortSignal,
): Promise<ArtifactListResponse> {
  const response = await fetch(`${API_BASE_URL}/api/artifacts`, {
    headers: authHeaders(idToken),
    signal,
  });

  if (!response.ok) await throwArtifactError(response);
  return response.json();
}

export async function getArtifact(
  artifactId: string,
  idToken: string,
  signal?: AbortSignal,
): Promise<SavedArtifact> {
  const response = await fetch(
    `${API_BASE_URL}/api/artifacts/${encodeURIComponent(artifactId)}`,
    { headers: authHeaders(idToken), signal },
  );

  if (!response.ok) await throwArtifactError(response);
  return response.json();
}

export async function deleteArtifact(
  artifactId: string,
  idToken: string,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/artifacts/${encodeURIComponent(artifactId)}`,
    { method: "DELETE", headers: authHeaders(idToken), signal },
  );

  if (!response.ok && response.status !== 204) await throwArtifactError(response);
}
