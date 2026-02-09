"use client";
import { useState } from "react";

interface CostItem {
  step: string;
  model: string;
  count: number;
  unit_cost: number;
  total: number;
}

interface BudgetVariant {
  tier: string;
  total_estimate: number;
  model_selections: Record<string, string>;
  cost_breakdown: CostItem[];
  tradeoffs: string;
}

interface Props {
  variants: BudgetVariant[];
  onSelect: (tier: string) => void;
}

const TIER_COLORS: Record<string, { border: string; bg: string; badge: string }> = {
  budget: {
    border: "border-green-700/50",
    bg: "bg-green-900/10",
    badge: "bg-green-500/20 text-green-400",
  },
  standard: {
    border: "border-blue-700/50",
    bg: "bg-blue-900/10",
    badge: "bg-blue-500/20 text-blue-400",
  },
  premium: {
    border: "border-amber-700/50",
    bg: "bg-amber-900/10",
    badge: "bg-amber-500/20 text-amber-400",
  },
};

export default function BudgetSelector({ variants, onSelect }: Props) {
  const [selected, setSelected] = useState<string>("standard");
  const [expandedTier, setExpandedTier] = useState<string | null>(null);

  const handleSelect = (tier: string) => {
    setSelected(tier);
  };

  const handleConfirm = () => {
    onSelect(selected);
  };

  return (
    <div className="mx-2 space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {variants.map((v) => {
          const tier = v.tier;
          const colors = TIER_COLORS[tier] || TIER_COLORS.standard;
          const isSelected = selected === tier;

          return (
            <button
              key={tier}
              type="button"
              onClick={() => handleSelect(tier)}
              className={`text-left p-3 rounded-xl border transition-all ${
                isSelected
                  ? `${colors.border} ${colors.bg} ring-1 ring-white/20`
                  : "border-gray-700 bg-gray-900/50 hover:border-gray-600"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-medium uppercase tracking-wider ${colors.badge}`}
                >
                  {tier}
                </span>
                <span className="text-sm font-bold text-white">
                  ${v.total_estimate.toFixed(2)}
                </span>
              </div>

              <p className="text-xs text-gray-400 mb-2">{v.tradeoffs}</p>

              {/* Cost breakdown toggle */}
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setExpandedTier(expandedTier === tier ? null : tier);
                }}
                className="text-[10px] text-gray-500 hover:text-gray-400 underline"
              >
                {expandedTier === tier ? "Hide details" : "Show breakdown"}
              </button>

              {expandedTier === tier && v.cost_breakdown.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-700/50 space-y-1">
                  {v.cost_breakdown.map((item, i) => (
                    <div key={i} className="flex justify-between text-[10px]">
                      <span className="text-gray-500 truncate mr-2">
                        {item.step} ({item.model})
                      </span>
                      <span className="text-gray-400 whitespace-nowrap">
                        {item.count}x ${item.unit_cost.toFixed(2)} = ${item.total.toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </button>
          );
        })}
      </div>

      <button
        type="button"
        onClick={handleConfirm}
        className="w-full py-2 rounded-lg text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 transition-all"
      >
        Approve with {selected.charAt(0).toUpperCase() + selected.slice(1)} Budget
      </button>
    </div>
  );
}
