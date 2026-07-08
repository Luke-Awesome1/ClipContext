"use client";

import { motion } from "framer-motion";

export type CandidatePool = "titles" | "descriptions" | "hashtags";

const POOL_LABELS: Record<CandidatePool, string> = {
  titles: "Titles",
  descriptions: "Descriptions",
  hashtags: "Hashtags",
};

const POOLS: CandidatePool[] = ["titles", "descriptions", "hashtags"];

interface CaptionTabsProps {
  active: CandidatePool;
  onChange: (pool: CandidatePool) => void;
  size?: "sm" | "md";
}

export default function CaptionTabs({
  active,
  onChange,
  size = "md",
}: CaptionTabsProps) {
  const pad = size === "sm" ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm";

  return (
    <div className="flex flex-wrap gap-2">
      {POOLS.map((pool) => {
        const isActive = active === pool;
        return (
          <button
            key={pool}
            type="button"
            onClick={() => onChange(pool)}
            className={`relative rounded-lg font-medium transition-colors ${pad} ${
              isActive
                ? "text-[#365f53]"
                : "text-neutral-600 hover:bg-neutral-100 hover:text-neutral-950"
            }`}
          >
            {isActive && (
              <motion.span
                layoutId="caption-tab-highlight"
                className="absolute inset-0 rounded-lg bg-[#365f53]/10 ring-1 ring-[#365f53]/25"
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
              />
            )}
            <span className="relative">{POOL_LABELS[pool]}</span>
          </button>
        );
      })}
    </div>
  );
}
