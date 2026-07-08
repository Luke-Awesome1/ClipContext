import type {
  JobCreateResponse,
  JobStatusResponse,
  Platform,
} from "@/types/video";

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

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") return data.detail;
  } catch {
    // response body was not JSON; fall through to generic message
  }
  return `Request failed with status ${response.status}`;
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
