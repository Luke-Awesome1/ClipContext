export type Platform = "youtube" | "web";

export type JobStatus = "queued" | "processing" | "completed" | "failed";

export type PipelineStageId =
  | "queued"
  | "validating"
  | "extracting_audio"
  | "extracting_frames"
  | "transcribing"
  | "temporal_alignment"
  | "visual_analysis"
  | "context_generation"
  | "worldwide_trends"
  | "creator_trends"
  | "content_generation"
  | "ranking"
  | "completed";

export const PIPELINE_STAGE_LABELS: Record<PipelineStageId, string> = {
  queued: "Queued",
  validating: "Validating video",
  extracting_audio: "Extracting audio",
  extracting_frames: "Scanning frames locally",
  transcribing: "Transcribing speech",
  temporal_alignment: "Building temporal windows",
  visual_analysis: "Analysing sparse visual evidence",
  context_generation: "Building canonical VideoContext",
  worldwide_trends: "Analysing worldwide trends",
  creator_trends: "Analysing creator trends",
  content_generation: "Generating titles, descriptions, hashtags",
  ranking: "Ranking generated candidates",
  completed: "Complete",
};

export const PIPELINE_STAGE_ORDER: PipelineStageId[] = [
  "queued",
  "validating",
  "extracting_audio",
  "extracting_frames",
  "transcribing",
  "temporal_alignment",
  "visual_analysis",
  "context_generation",
  "worldwide_trends",
  "creator_trends",
  "content_generation",
  "ranking",
  "completed",
];

export interface TextCandidate {
  id: number;
  text: string;
}

export interface HashtagCandidate {
  id: number;
  tags: string[];
}

export interface GeneratedContent {
  titles: TextCandidate[];
  descriptions: TextCandidate[];
  hashtags: HashtagCandidate[];
}

export interface RankedCandidate {
  id: number;
  rank: number;
  score: number;
  reason: string;
}

export interface Rankings {
  titles: RankedCandidate[];
  descriptions: RankedCandidate[];
  hashtags: RankedCandidate[];
}

export interface VideoContextSummary {
  topic: string;
  content_type: string;
  multimodal_summary: string;
  core_message: string;
}

export interface PipelineResult {
  job_id: string;
  video_context: VideoContextSummary;
  generated_content: GeneratedContent;
  rankings: Rankings;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  stage: PipelineStageId;
  progress: number;
  message: string;
  result: PipelineResult | null;
  error: string | null;
}

export interface JobCreateResponse {
  job_id: string;
  status: JobStatus;
}

export interface CreatorContext {
  youtubeChannelUrl: string;
}
