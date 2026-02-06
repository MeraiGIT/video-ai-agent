"use client";
import { useState } from "react";

interface Scene {
  scene_number: number;
  narration: string;
  visual_description: string;
  image_prompt: string;
  duration: number;
}

interface Props {
  scenes: Scene[];
  totalDuration: number;
}

export default function SceneCards({ scenes, totalDuration }: Props) {
  const [expandedPrompt, setExpandedPrompt] = useState<number | null>(null);

  return (
    <div className="animate-slide-up mx-2 space-y-2">
      {/* Header */}
      <div className="flex items-center gap-2 px-1">
        <div className="w-1.5 h-1.5 rounded-full bg-purple-400" />
        <span className="text-xs font-medium text-gray-300 uppercase tracking-wider">
          Scene Plan
        </span>
        <span className="ml-auto text-xs text-gray-500">
          {scenes.length} scenes / {totalDuration}s
        </span>
      </div>

      {/* Scene cards */}
      <div className="space-y-2">
        {scenes.map((scene, i) => (
          <div
            key={i}
            className="rounded-xl border border-gray-700 bg-gray-900 p-3 space-y-2"
          >
            <div className="flex items-start gap-3">
              {/* Scene number */}
              <div className="w-7 h-7 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center text-xs font-bold flex-shrink-0">
                {scene.scene_number}
              </div>

              <div className="flex-1 min-w-0 space-y-1.5">
                {/* Narration */}
                <p className="text-sm text-gray-300 italic leading-relaxed">
                  &ldquo;{scene.narration}&rdquo;
                </p>

                {/* Visual */}
                <p className="text-xs text-gray-500">
                  {scene.visual_description}
                </p>

                {/* Duration + expand prompt */}
                <div className="flex items-center gap-2">
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-800 text-gray-400 border border-gray-700">
                    {scene.duration}s
                  </span>
                  <button
                    type="button"
                    onClick={() =>
                      setExpandedPrompt(expandedPrompt === i ? null : i)
                    }
                    className="text-[10px] text-blue-400 hover:text-blue-300 transition"
                  >
                    {expandedPrompt === i ? "Hide prompt" : "Show prompt"}
                  </button>
                </div>

                {/* Expanded image prompt */}
                {expandedPrompt === i && (
                  <div className="text-xs text-gray-600 bg-gray-800/50 rounded-lg p-2 mt-1">
                    {scene.image_prompt}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
