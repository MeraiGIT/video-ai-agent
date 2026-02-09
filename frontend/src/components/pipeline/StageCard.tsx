"use client";

import type { PipelineStage } from "@/lib/types";

interface Props {
  stage: PipelineStage;
  isActive: boolean;
  onClick?: () => void;
}

const STATUS_ICONS: Record<string, string> = {
  pending: "○",
  active: "◉",
  completed: "✓",
  failed: "✗",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "text-gray-500 border-gray-700",
  active: "text-blue-400 border-blue-500/50 bg-blue-950/30",
  completed: "text-emerald-400 border-emerald-700/50",
  failed: "text-red-400 border-red-700/50",
};

const ICON_COLORS: Record<string, string> = {
  pending: "text-gray-600",
  active: "text-blue-400",
  completed: "text-emerald-400",
  failed: "text-red-400",
};

export default function StageCard({ stage, isActive, onClick }: Props) {
  const statusColor = STATUS_COLORS[stage.status] || STATUS_COLORS.pending;
  const iconColor = ICON_COLORS[stage.status] || ICON_COLORS.pending;
  const icon = STATUS_ICONS[stage.status] || "○";
  const clickable = stage.status === "completed" && onClick;

  return (
    <button
      type="button"
      onClick={clickable ? onClick : undefined}
      disabled={!clickable}
      className={`w-full text-left px-3 py-2.5 rounded-lg border transition-all duration-200 ${statusColor} ${
        clickable ? "cursor-pointer hover:bg-gray-800/50" : "cursor-default"
      } ${isActive ? "ring-1 ring-blue-500/30" : ""}`}
    >
      <div className="flex items-center gap-2.5">
        <span className={`text-sm font-mono ${iconColor} ${isActive ? "animate-pulse" : ""}`}>
          {icon}
        </span>

        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium truncate">{stage.name}</p>

          {/* Substep progress dots */}
          {stage.substeps && stage.substeps.length > 0 && (
            <div className="flex gap-0.5 mt-1">
              {stage.substeps.map((sub, i) => (
                <div
                  key={i}
                  className={`w-1.5 h-1.5 rounded-full ${
                    sub.status === "completed"
                      ? "bg-emerald-400"
                      : sub.status === "active"
                        ? "bg-blue-400 animate-pulse"
                        : "bg-gray-700"
                  }`}
                  title={sub.name}
                />
              ))}
            </div>
          )}
        </div>

        {/* Cost badge */}
        {stage.cost != null && stage.cost > 0 && (
          <span className="text-[10px] text-gray-500 font-mono tabular-nums">
            ${stage.cost.toFixed(2)}
          </span>
        )}

        {/* Asset count */}
        {stage.assetsCount != null && stage.assetsCount > 0 && (
          <span className="text-[10px] text-gray-500">
            {stage.assetsCount}
          </span>
        )}
      </div>
    </button>
  );
}
