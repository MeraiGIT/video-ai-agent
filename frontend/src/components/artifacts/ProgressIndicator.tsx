"use client";
import type { ProgressUpdate } from "@/lib/types";

interface Props {
  progress: ProgressUpdate;
}

export default function ProgressIndicator({ progress }: Props) {
  const hasNumerics = progress.current != null && progress.total != null && progress.total > 0;
  const pct = hasNumerics ? Math.round((progress.current! / progress.total!) * 100) : 0;

  return (
    <div className="mx-2 px-4 py-3 rounded-xl bg-gray-900/80 border border-gray-700/50">
      <div className="flex items-center gap-3">
        {/* Pulsing dots */}
        <div className="flex gap-1">
          <div className="w-1.5 h-1.5 rounded-full bg-blue-400 dot-1" />
          <div className="w-1.5 h-1.5 rounded-full bg-blue-400 dot-2" />
          <div className="w-1.5 h-1.5 rounded-full bg-blue-400 dot-3" />
        </div>

        <span className="text-sm text-gray-300 flex-1">{progress.message}</span>

        {hasNumerics && (
          <span className="text-xs text-gray-500">
            {progress.current} / {progress.total}
          </span>
        )}
      </div>

      {hasNumerics && (
        <div className="mt-2 h-1 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full progress-fill"
            style={{ width: `${pct}%` }}
          />
        </div>
      )}
    </div>
  );
}
