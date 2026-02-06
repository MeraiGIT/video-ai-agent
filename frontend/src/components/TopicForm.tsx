"use client";
import { useState, useRef, useCallback } from "react";
import type { VideoModel, UploadedFile } from "@/lib/types";
import { VIDEO_MODELS } from "@/lib/types";

interface Props {
  onSubmit: (
    topic: string,
    model: VideoModel,
    concatEnabled: boolean,
    uploadedFileUrls?: string[]
  ) => void;
}

export default function TopicForm({ onSubmit }: Props) {
  const [topic, setTopic] = useState("");
  const [model, setModel] = useState<VideoModel>("seedance");
  const [concatEnabled, setConcatEnabled] = useState(true);
  const [uploads, setUploads] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback((files: FileList | File[]) => {
    const newUploads: UploadedFile[] = [];
    for (const file of Array.from(files)) {
      if (!file.type.startsWith("image/") && !file.type.startsWith("video/")) continue;
      const preview = file.type.startsWith("image/")
        ? URL.createObjectURL(file)
        : undefined;
      newUploads.push({
        url: URL.createObjectURL(file), // local preview URL, will be replaced after upload
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
    // Note: actual file upload happens via the upload endpoint after session creation.
    // For now, we pass empty URLs — the upload flow will be enhanced in future.
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

        {/* File Upload Area */}
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
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
            accept="image/*,video/*"
            className="hidden"
            onChange={(e) => e.target.files && handleFiles(e.target.files)}
          />
          <svg className="w-6 h-6 text-gray-500 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 16v-8m0 0l-3 3m3-3l3 3M3 16v2a2 2 0 002 2h14a2 2 0 002-2v-2" />
          </svg>
          <span className="text-xs text-gray-500">
            Drop images/videos here or click to upload
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
                    <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </div>
                )}
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); removeUpload(i); }}
                  className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-red-600 text-white text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition"
                >
                  &times;
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Model Selector */}
        <div className="space-y-2">
          <label className="text-sm text-gray-400 font-medium">
            Video Model
          </label>
          <div className="grid grid-cols-2 gap-3">
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
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium text-white">{m.name}</div>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                    m.provider === "fal.ai"
                      ? "bg-purple-500/20 text-purple-400"
                      : "bg-emerald-500/20 text-emerald-400"
                  }`}>
                    {m.provider}
                  </span>
                </div>
                <div className="text-xs text-gray-400 mt-1">{m.cost}</div>
                <div className="text-xs text-gray-500 mt-0.5">{m.description}</div>
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
