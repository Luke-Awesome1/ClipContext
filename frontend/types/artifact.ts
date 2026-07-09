import type { GeneratedContent, Rankings, VideoContextSummary } from "@/types/video";

export interface ArtifactCreateRequest {
  job_id: string;
  selected_title_id: number;
  selected_description_id: number;
  selected_hashtag_set_id: number;
  video_display_name?: string | null;
}

export interface ArtifactSelection {
  title_id: number;
  description_id: number;
  hashtag_set_id: number;
}

export interface ArtifactVideoInfo {
  original_filename: string | null;
  display_name: string | null;
}

export interface SavedYouTubeUploadMetadata {
  uploaded: boolean;
  video_id: string | null;
  video_url: string | null;
  privacy_status: string | null;
  channel_id: string | null;
  channel_title: string | null;
  uploaded_at: string | null;
}

export interface SavedArtifact {
  artifact_id: string;
  source_job_id: string;
  created_at: string;
  updated_at: string;
  video: ArtifactVideoInfo;
  video_context: VideoContextSummary;
  generated_content: GeneratedContent;
  rankings: Rankings;
  selection: ArtifactSelection;
  youtube_upload: SavedYouTubeUploadMetadata;
}

export interface ArtifactSummary {
  artifact_id: string;
  created_at: string;
  topic: string;
  content_type: string;
  selected_title: string;
  youtube_uploaded: boolean;
}

export interface ArtifactListResponse {
  artifacts: ArtifactSummary[];
}

export interface ArtifactApiErrorDetail {
  code: string;
  message: string;
}
