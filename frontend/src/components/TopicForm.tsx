"use client";
import { useState } from "react";
import type { VideoModel } from "@/lib/types";
import { VIDEO_MODELS } from "@/lib/types";

interface Props {
  onSubmit: (topic: string, model: VideoModel, concatEnabled: boolean) => void;
}

export default function TopicForm({ onSubmit }: Props) {
  const [topic, setTopic] = useState("");
  const [model, setModel] = useState<VideoModel>("seedance");
  const [concatEnabled, setConcatEnabled] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    onSubmit(topic.trim(), model, concatEnabled);
  };

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-72px)] p-6">
      <form onSubmit={handleSubmit} className="w-full max-w-xl space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Create Your Video
          </h2>
          <p className="text-gray-400 text-sm">
            Enter a topic and I&apos;ll guide you through each step
          </p>
        </div>

        {/* Topic Input */}
        <div>
          <textarea
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g., 3 tips for better sleep, How AI is changing healthcare..."
            className="w-full h-28 px-4 py-3 rounded-xl bg-gray-900 border border-gray-700 text-white placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition"
          />
        </div>

        {/* Model Selector */}
        <div className="space-y-2">
          <label className="text-sm text-gray-400 font-medium">
            Video Model
          </label>
          <div className="grid grid-cols-3 gap-3">
            {VIDEO_MODELS.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => setModel(m.id)}
                className={`p-3 rounded-xl border text-left transition-all ${
                  model === m.id
                    ? "border-blue-500 bg-blue-500/10 ring-1 ring-blue-500/30"
                    : "border-gray-700 bg-gray-900 hover:border-gray-600"
                }`}
              >
                <div className="text-sm font-medium text-white">{m.name}</div>
                <div className="text-xs text-gray-400 mt-1">{m.cost}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Concat Toggle */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-gray-900 border border-gray-700">
          <div>
            <div className="text-sm font-medium text-white">
              Assemble into single video
            </div>
            <div className="text-xs text-gray-400">
              Concatenate all scenes with voiceover and captions
            </div>
          </div>
          <button
            type="button"
            onClick={() => setConcatEnabled(!concatEnabled)}
            className={`relative w-12 h-6 rounded-full transition-colors ${
              concatEnabled ? "bg-blue-500" : "bg-gray-600"
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                concatEnabled ? "translate-x-6" : ""
              }`}
            />
          </button>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={!topic.trim()}
          className="w-full py-3 rounded-xl font-medium text-white bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          Start Creating
        </button>
      </form>
    </div>
  );
}
