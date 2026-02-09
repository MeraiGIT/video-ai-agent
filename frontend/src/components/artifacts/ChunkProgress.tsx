"use client";

interface Props {
  currentChunk: number;
  totalChunks: number;
  chapterTitle?: string;
}

export default function ChunkProgress({
  currentChunk,
  totalChunks,
  chapterTitle,
}: Props) {
  const pct = totalChunks > 0 ? Math.round(((currentChunk + 1) / totalChunks) * 100) : 0;

  return (
    <div className="mx-2 px-4 py-3 rounded-xl bg-indigo-950/30 border border-indigo-800/30">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-indigo-300">
          Chapter {currentChunk + 1} of {totalChunks}
        </span>
        {chapterTitle && (
          <span className="text-xs text-indigo-400 truncate ml-2">
            {chapterTitle}
          </span>
        )}
      </div>

      <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-indigo-500 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="flex justify-between mt-1">
        {Array.from({ length: totalChunks }).map((_, i) => (
          <div
            key={i}
            className={`w-2 h-2 rounded-full ${
              i < currentChunk
                ? "bg-indigo-400"
                : i === currentChunk
                  ? "bg-indigo-500 animate-pulse"
                  : "bg-gray-700"
            }`}
            title={`Chapter ${i + 1}`}
          />
        ))}
      </div>
    </div>
  );
}
