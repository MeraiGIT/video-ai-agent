"use client";

import type { PipelineStage } from "@/lib/types";
import StageCard from "./StageCard";
import CostTracker from "./CostTracker";

const DEFAULT_STAGES: PipelineStage[] = [
  { name: "Intake", status: "pending" },
  { name: "Research", status: "pending" },
  { name: "Creative Direction", status: "pending" },
  { name: "Blueprint", status: "pending" },
  { name: "Produce", status: "pending" },
  { name: "Assemble", status: "pending" },
  { name: "Polish", status: "pending" },
  { name: "Deliver", status: "pending" },
];

interface Props {
  stages: PipelineStage[];
  currentCost: number;
  budgetLimit: number;
  onStageClick?: (index: number) => void;
}

export default function PipelineSidebar({
  stages,
  currentCost,
  budgetLimit,
  onStageClick,
}: Props) {
  const displayStages = stages.length > 0 ? stages : DEFAULT_STAGES;

  // Find the active stage index
  const activeIndex = displayStages.findIndex((s) => s.status === "active");

  // Calculate completed count
  const completedCount = displayStages.filter(
    (s) => s.status === "completed"
  ).length;

  return (
    <aside className="w-56 flex-shrink-0 border-r border-gray-800/50 bg-gray-950/50 flex flex-col h-[calc(100vh-72px)]">
      {/* Header */}
      <div className="px-3 py-3 border-b border-gray-800/50">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
            Pipeline
          </h2>
          <span className="text-[10px] text-gray-600 font-mono">
            {completedCount}/{displayStages.length}
          </span>
        </div>

        {/* Overall progress bar */}
        <div className="mt-2 h-1 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full transition-all duration-500"
            style={{
              width: `${(completedCount / displayStages.length) * 100}%`,
            }}
          />
        </div>
      </div>

      {/* Stage list */}
      <div className="flex-1 overflow-y-auto px-2 py-2 space-y-1">
        {displayStages.map((stage, i) => (
          <StageCard
            key={stage.name}
            stage={stage}
            isActive={i === activeIndex}
            onClick={
              stage.status === "completed" && onStageClick
                ? () => onStageClick(i)
                : undefined
            }
          />
        ))}
      </div>

      {/* Cost tracker at bottom */}
      <div className="border-t border-gray-800/50">
        <CostTracker currentCost={currentCost} budgetLimit={budgetLimit} />
      </div>
    </aside>
  );
}
