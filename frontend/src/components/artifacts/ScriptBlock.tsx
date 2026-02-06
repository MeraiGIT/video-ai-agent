"use client";

interface Props {
  content: string;
  wordCount: number;
}

export default function ScriptBlock({ content, wordCount }: Props) {
  return (
    <div className="animate-slide-up mx-2">
      <div className="rounded-xl border border-gray-700 bg-gray-900 overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-700/50 bg-gray-800/50">
          <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
          <span className="text-xs font-medium text-gray-300 uppercase tracking-wider">
            Script
          </span>
          <span className="ml-auto text-xs text-gray-500">
            {wordCount} words
          </span>
        </div>

        {/* Body */}
        <div className="px-4 py-3 border-l-2 border-blue-500/40">
          <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">
            {content}
          </div>
        </div>
      </div>
    </div>
  );
}
