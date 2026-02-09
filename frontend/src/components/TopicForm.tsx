"use client";
import { useState, useRef, useCallback } from "react";
import type { UploadedFile } from "@/lib/types";

interface Props {
  onSubmit: (topic: string, uploadedFileUrls?: string[]) => void;
}

export default function TopicForm({ onSubmit }: Props) {
  const [topic, setTopic] = useState("");
  const [uploads, setUploads] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback((files: FileList | File[]) => {
    const newUploads: UploadedFile[] = [];
    for (const file of Array.from(files)) {
      if (
        !file.type.startsWith("image/") &&
        !file.type.startsWith("video/") &&
        !file.type.startsWith("audio/")
      )
        continue;
      const preview = file.type.startsWith("image/")
        ? URL.createObjectURL(file)
        : undefined;
      newUploads.push({
        url: URL.createObjectURL(file),
        type: file.type,
        filename: file.name,
        preview,
      });
    }
    setUploads((prev) => [...prev, ...newUploads]);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const removeUpload = (index: number) => {
    setUploads((prev) => {
      const removed = prev[index];
      if (removed.preview) URL.revokeObjectURL(removed.preview);
      return prev.filter((_, i) => i !== index);
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    onSubmit(topic.trim());
  };

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-72px)] p-6">
      <form onSubmit={handleSubmit} className="w-full max-w-xl space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            AI Production Studio
          </h2>
          <p className="text-gray-400 text-sm">
            Describe what you want to create &mdash; video, graphic, audio, or anything creative
          </p>
        </div>

        {/* Creative Brief Input */}
        <div>
          <textarea
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Describe what you want to create. Be as specific as you want — I'll ask if I need more info.

Examples:
• A 30-second TikTok about morning routines
• A YouTube thumbnail for my cooking channel
• A cinematic product video for a new sneaker
• Recreate this video in a different style (upload a reference)"
            className="w-full h-36 px-4 py-3 rounded-xl bg-gray-900 border border-gray-700 text-white placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition"
          />
        </div>

        {/* File Upload Area */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`relative flex flex-col items-center justify-center px-4 py-4 rounded-xl border-2 border-dashed cursor-pointer transition-all ${
            isDragging
              ? "border-blue-500 bg-blue-500/10"
              : "border-gray-700 bg-gray-900/50 hover:border-gray-600"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*,video/*,audio/*"
            className="hidden"
            onChange={(e) => e.target.files && handleFiles(e.target.files)}
          />
          <svg
            className="w-6 h-6 text-gray-500 mb-1"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M12 16v-8m0 0l-3 3m3-3l3 3M3 16v2a2 2 0 002 2h14a2 2 0 002-2v-2"
            />
          </svg>
          <span className="text-xs text-gray-500">
            Drop images, videos, or audio here — or click to upload references
          </span>
        </div>

        {/* Upload Previews */}
        {uploads.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {uploads.map((u, i) => (
              <div key={i} className="relative group">
                {u.preview ? (
                  <img
                    src={u.preview}
                    alt={u.filename}
                    className="w-16 h-16 rounded-lg object-cover border border-gray-700"
                  />
                ) : (
                  <div className="w-16 h-16 rounded-lg bg-gray-800 border border-gray-700 flex items-center justify-center">
                    {u.type.startsWith("video/") ? (
                      <svg
                        className="w-5 h-5 text-gray-500"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                        />
                      </svg>
                    ) : (
                      <svg
                        className="w-5 h-5 text-gray-500"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
                        />
                      </svg>
                    )}
                  </div>
                )}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeUpload(i);
                  }}
                  className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-red-600 text-white text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition"
                >
                  &times;
                </button>
              </div>
            ))}
          </div>
        )}

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
