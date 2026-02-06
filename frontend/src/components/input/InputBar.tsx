"use client";
import { useState } from "react";
import type { AwaitingState } from "@/lib/types";

interface Props {
  awaiting: AwaitingState | null;
  isProcessing: boolean;
  onApprove: () => void;
  onModify: (message: string) => void;
  onRegenerate: (indices: number[]) => void;
}

export default function InputBar({
  awaiting,
  isProcessing,
  onApprove,
  onModify,
  onRegenerate,
}: Props) {
  const [text, setText] = useState("");
  const [regenIndex, setRegenIndex] = useState("");

  const handleSend = () => {
    const msg = text.trim();
    if (!msg) return;
    onModify(msg);
    setText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleRegenerate = () => {
    const indices = regenIndex
      .split(",")
      .map((s) => parseInt(s.trim(), 10) - 1)
      .filter((n) => !isNaN(n) && n >= 0);
    if (indices.length === 0) return;
    onRegenerate(indices);
    setRegenIndex("");
  };

  const disabled = isProcessing || !awaiting;
  const showRegenerate =
    awaiting &&
    (awaiting.stage === "images_review" || awaiting.stage === "videos_review");

  return (
    <div className="border-t border-gray-800 bg-gray-950 px-4 py-3">
      {/* Action buttons row */}
      {awaiting && !isProcessing && (
        <div className="flex items-center gap-2 mb-2">
          <button
            type="button"
            onClick={onApprove}
            className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition"
          >
            Approve & Continue
          </button>

          {showRegenerate && (
            <div className="flex items-center gap-1.5 ml-auto">
              <input
                value={regenIndex}
                onChange={(e) => setRegenIndex(e.target.value)}
                placeholder="Scene # (e.g. 1,3)"
                className="w-36 px-2.5 py-1.5 rounded-lg bg-gray-800 border border-gray-700 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-orange-500/50"
              />
              <button
                type="button"
                onClick={handleRegenerate}
                disabled={!regenIndex.trim()}
                className="px-3 py-1.5 rounded-lg bg-orange-600 hover:bg-orange-500 disabled:opacity-40 text-white text-sm font-medium transition"
              >
                Regenerate
              </button>
            </div>
          )}
        </div>
      )}

      {/* Text input row */}
      <div className="flex items-end gap-2">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={
            disabled
              ? "Waiting..."
              : "Suggest changes (e.g. 'make it funnier', 'more dramatic')"
          }
          rows={1}
          className="flex-1 px-4 py-2.5 rounded-xl bg-gray-900 border border-gray-700 text-white text-sm placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 disabled:opacity-40 transition"
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-30 text-white transition flex-shrink-0"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
    </div>
  );
}
