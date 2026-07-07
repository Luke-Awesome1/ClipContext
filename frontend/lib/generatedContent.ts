import type { CaptionStyle, VideoAnalysis } from "@/types/video";

export const PIPELINE_STAGES = [
  { id: "speech" as const, label: "Understanding Speech", durationMs: 2200 },
  { id: "visual" as const, label: "Understanding Visual Frames", durationMs: 2600 },
  { id: "context" as const, label: "Building Unified Context", durationMs: 2000 },
  { id: "title" as const, label: "Generating Title", durationMs: 1400 },
  { id: "caption" as const, label: "Generating Caption", durationMs: 1600 },
  { id: "summary" as const, label: "Generating Summary", durationMs: 1200 },
  { id: "hashtags" as const, label: "Generating Hashtags", durationMs: 1000 },
];

const outputs: Record<CaptionStyle, VideoAnalysis["outputs"][CaptionStyle]> = {
  Formal: {
    title: "Three Frameworks for Sustainable Product-Led Growth",
    caption:
      "In this walkthrough, the founder breaks down how early-stage teams can align onboarding, activation, and expansion into one measurable growth loop — with live dashboard examples from their Q1 rollout.",
    summary:
      "A structured founder-led explainer covering product-led growth mechanics. Lumina detected spoken frameworks, on-screen analytics, and emphasis on retention metrics to produce a publication-ready formal caption suited for LinkedIn or YouTube descriptions.",
    hashtags: [
      "#ProductLedGrowth",
      "#StartupStrategy",
      "#SaaS",
      "#FounderTips",
      "#GrowthMarketing",
      "#B2BSaaS",
      "#Onboarding",
      "#Retention",
    ],
  },
  Sarcastic: {
    title: "Another PLG Video. Somehow Still Useful.",
    caption:
      "Oh great, another founder explaining growth loops like it's a TED talk — except this one actually shows the dashboard, names the metrics, and doesn't say \"synergy\" once. Shocking.",
    summary:
      "Dry, self-aware tone for audiences who scroll past generic startup advice. Visual cues (live charts, Q1 overlay) and confident delivery informed a caption that sounds sharp without losing the substance.",
    hashtags: [
      "#StartupLife",
      "#PLG",
      "#FounderReality",
      "#SaaSHumor",
      "#BuildInPublic",
      "#NotAnotherPitch",
      "#GrowthLoop",
      "#TechTwitter",
    ],
  },
  "Humor-T": {
    title: "POV: ur growth loop actually loops 💀",
    caption:
      "bro really said \"let me cook\" and pulled up THREE frameworks + the dashboard in 90 sec no cap 📈 onboarding → activation → expansion is giving main character arc and i'm here for it",
    summary:
      "Trend-forward voice tuned for Reels and TikTok. Fast pacing, direct-to-camera energy, and screen-recording segments mapped to short-form slang while keeping the core PLG message intact.",
    hashtags: [
      "#POV",
      "#StartupTok",
      "#PLG",
      "#SaaS",
      "#FounderLife",
      "#GrowthTips",
      "#TechTok",
      "#MainCharacterEnergy",
    ],
  },
  "Humor-NT": {
    title: "My Growth Loop Has More Steps Than My Morning Coffee Routine",
    caption:
      "So I'm watching this founder explain product-led growth and honestly? It's like making coffee. Grind the onboarding, brew the activation, and pray the expansion doesn't spill everywhere. Three frameworks. One dashboard. Zero regrets.",
    summary:
      "Classic, approachable humor without meme slang. Lumina matched the instructional tone and visual dashboard segments to a caption that works for Facebook, email newsletters, or audiences outside trend-heavy platforms.",
    hashtags: [
      "#StartupHumor",
      "#ProductLedGrowth",
      "#SmallBusiness",
      "#EntrepreneurLife",
      "#SaaSFounder",
      "#MarketingTips",
      "#CoffeeAndCode",
      "#WorkSmarter",
    ],
  },
};

export const DEMO_ANALYSIS: VideoAnalysis = {
  outputs,
  concepts: [
    { label: "Founder monologue — instructional tone", category: "speech", confidence: 96 },
    { label: "Screen recording: analytics dashboard", category: "visual", confidence: 94 },
    { label: "On-screen text overlay — \"Q1 Goals\"", category: "visual", confidence: 91 },
    { label: "Hand gestures during key points", category: "visual", confidence: 87 },
    { label: "Topic: product-led growth frameworks", category: "context", confidence: 98 },
    { label: "Pacing: moderate, segment-based", category: "context", confidence: 89 },
    { label: "Environment: modern office / desk setup", category: "visual", confidence: 85 },
    { label: "Call-to-action implied at outro", category: "speech", confidence: 82 },
  ],
};

export function getAnalysisForStyle(style: CaptionStyle) {
  return DEMO_ANALYSIS.outputs[style];
}

export function buildExportPayload(
  style: CaptionStyle,
  fileName: string | null,
) {
  const output = DEMO_ANALYSIS.outputs[style];
  return {
    fileName: fileName ?? "video",
    style,
    generatedAt: new Date().toISOString(),
    ...output,
    aiUnderstanding: DEMO_ANALYSIS.concepts,
  };
}
