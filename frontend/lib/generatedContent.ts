import type { PipelineResult, RankedCandidate } from "@/types/video";

// Demo-mode sample data only. Never used on the real upload -> job ->
// results path; that path always renders backend-sourced PipelineResult.
const DEMO_TITLES = [
  "The Dream You Hold Is Still Possible",
  "Your Dream Called. It Still Has Audacity.",
  "POV: the dream is still possible",
  "The Dream Is Running Late, Not Cancelled",
  "Why This Dream Refuses To Die",
  "I Almost Gave Up On This Dream",
  "The Quiet Case For Not Quitting",
  "This Is What Holding On Looks Like",
  "Dreams Don't Expire, You Just Got Tired",
  "One More Try: A Short Film On Persistence",
];

const DEMO_DESCRIPTIONS = [
  "A motivational short built around persistence, disappointment, and the belief that a dream can remain possible even when the path has been difficult.",
  "Sure, disappointment showed up uninvited. This video makes the case that the dream in your head still deserves another round.",
  "that dream in your head really said \"we are not done here.\" city window, big feelings, mountain shot, whole main character arc.",
  "Sometimes a dream feels like it missed the bus. This clip is the reminder that late does not mean impossible.",
  "A grounded look at what it feels like to keep going when a goal takes longer than expected.",
  "Speech and visuals combine to trace an emotional arc from doubt to renewed conviction.",
  "A short, quiet meditation on why some goals are worth the wait.",
  "On-screen text and visual pacing build a case for staying in motion.",
  "A reframe: dreams don't have deadlines, even when it feels that way.",
  "A closing note on persistence, built entirely from what's shown and said in the clip.",
];

const DEMO_HASHTAG_SETS = [
  ["#Motivation", "#Dreams", "#Mindset", "#PersonalGrowth", "#KeepGoing"],
  ["#MotivationTok", "#DreamBig", "#MindsetShift", "#Inspirational", "#SelfGrowth"],
  ["#POV", "#DreamLife", "#MainCharacterEnergy", "#HealingJourney", "#Inspiration"],
  ["#Resilience", "#LifeMotivation", "#KeepBelieving", "#MindsetMatters", "#ShortFormVideo"],
  ["#Perseverance", "#GoalSetting", "#NeverGiveUp", "#GrowthMindset", "#Shorts"],
  ["#EmotionalArc", "#Storytelling", "#CreatorTools", "#ClipContext", "#AMD"],
  ["#QuietMotivation", "#StillHere", "#OneMoreTry", "#KeepMoving", "#Purpose"],
  ["#OnScreenText", "#VisualStorytelling", "#MotivationalShort", "#Reflection", "#Growth"],
  ["#NoExpiration", "#Patience", "#TrustTheProcess", "#DreamsDontDie", "#Inspiration"],
  ["#ShortFilm", "#Persistence", "#RealTalk", "#KeepGoing", "#ClipContext"],
];

function buildRankings(count: number): RankedCandidate[] {
  return Array.from({ length: count }, (_, index) => ({
    id: index + 1,
    rank: index + 1,
    score: 96 - index * 3,
    reason:
      index === 0
        ? "Strongest contextual grounding and hook among the pool."
        : "Grounded in VideoContext with slightly less distinctive framing.",
  }));
}

export const DEMO_RESULT: PipelineResult = {
  job_id: "demo",
  video_context: {
    topic: "Persisting through a difficult personal goal",
    content_type: "Motivational short-form video",
    core_message: "A dream can remain possible even after disappointment.",
    multimodal_summary:
      "Speech about a dream remaining possible is paired with visible on-screen text (\"this is my ultimate dream\", \"I believe it's yours too\"), silhouetted indoor scenes, and a closing mountain-valley shot.",
  },
  generated_content: {
    titles: DEMO_TITLES.map((text, index) => ({ id: index + 1, text })),
    descriptions: DEMO_DESCRIPTIONS.map((text, index) => ({ id: index + 1, text })),
    hashtags: DEMO_HASHTAG_SETS.map((tags, index) => ({ id: index + 1, tags })),
  },
  rankings: {
    titles: buildRankings(10),
    descriptions: buildRankings(10),
    hashtags: buildRankings(10),
  },
  // Demo mode never ran real inference, AMD or otherwise — no AMD
  // indicator should render for it (see AIUnderstandingCard.tsx).
  ai_audit: [],
};
