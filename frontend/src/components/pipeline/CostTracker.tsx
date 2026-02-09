"use client";

interface Props {
  currentCost: number;
  budgetLimit: number;
}

export default function CostTracker({ currentCost, budgetLimit }: Props) {
  const pct = budgetLimit > 0 ? Math.min((currentCost / budgetLimit) * 100, 100) : 0;
  const isWarning = pct >= 80;
  const isOver = pct >= 100;

  const barColor = isOver
    ? "bg-red-500"
    : isWarning
      ? "bg-amber-500"
      : "bg-emerald-500";

  const textColor = isOver
    ? "text-red-400"
    : isWarning
      ? "text-amber-400"
      : "text-gray-400";

  return (
    <div className="px-3 py-2">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[10px] uppercase tracking-wider text-gray-500 font-medium">
          Cost
        </span>
        <span className={`text-xs font-mono tabular-nums ${textColor}`}>
          ${currentCost.toFixed(2)}
          {budgetLimit > 0 && (
            <span className="text-gray-600"> / ${budgetLimit.toFixed(2)}</span>
          )}
        </span>
      </div>

      {budgetLimit > 0 && (
        <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${barColor}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      )}

      {isWarning && !isOver && (
        <p className="text-[10px] text-amber-500 mt-1">Approaching budget limit</p>
      )}
      {isOver && (
        <p className="text-[10px] text-red-500 mt-1">Budget limit exceeded</p>
      )}
    </div>
  );
}
