"use client";

import { motion } from "framer-motion";
import { CAPTION_STYLES, type CaptionStyle } from "@/types/video";

interface CaptionTabsProps {
  active: CaptionStyle;
  onChange: (style: CaptionStyle) => void;
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
      {CAPTION_STYLES.map((style) => {
        const isActive = active === style;
        return (
          <button
            key={style}
            type="button"
            onClick={() => onChange(style)}
            className={`relative rounded-lg font-medium transition-colors ${pad} ${
              isActive
                ? "text-blue-300"
                : "text-neutral-400 hover:bg-white/[0.05] hover:text-neutral-200"
            }`}
          >
            {isActive && (
              <motion.span
                layoutId="caption-tab-highlight"
                className="absolute inset-0 rounded-lg bg-blue-500/20 shadow-[0_0_24px_rgba(59,130,246,0.16)] ring-1 ring-blue-400/30"
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
              />
            )}
            <span className="relative">{style}</span>
          </button>
        );
      })}
    </div>
  );
}
