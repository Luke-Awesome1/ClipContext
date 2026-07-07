export const CAPTION_STYLES = [
  "Formal",
  "Sarcastic",
  "Humor-T",
  "Humor-NT",
] as const;

export type CaptionStyle = (typeof CAPTION_STYLES)[number];

export interface GeneratedOutput {
  title: string;
  caption: string;
  summary: string;
  hashtags: string[];
}

export interface DetectedConcept {
  label: string;
  category: "speech" | "visual" | "context";
  confidence: number;
}

export interface VideoAnalysis {
  outputs: Record<CaptionStyle, GeneratedOutput>;
  concepts: DetectedConcept[];
}

export type PipelineStageId =
  | "speech"
  | "visual"
  | "context"
  | "title"
  | "caption"
  | "summary"
  | "hashtags";

export interface PipelineStage {
  id: PipelineStageId;
  label: string;
  durationMs: number;
}

export interface CreatorContext {
  youtubeChannelUrl: string;
  useCreatorContext: boolean;
}
