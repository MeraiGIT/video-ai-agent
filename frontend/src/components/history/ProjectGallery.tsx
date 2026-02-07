"use client";

import { useState } from "react";
import type { ProjectWithMedia, MediaItem } from "@/lib/api";
import { deleteMediaItem } from "@/lib/api";

interface Props {
  project: ProjectWithMedia;
  onBack: () => void;
  onDeleteProject: () => void;
  onMediaDeleted: (mediaId: string) => void;
}

function MediaCard({
  item,
  onDelete,
}: {
  item: MediaItem;
  onDelete: () => void;
}) {
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <div className="group relative rounded-lg overflow-hidden border border-gray-800 bg-gray-900">
      {item.type === "image" && item.public_url && (
        <img
          src={item.public_url}
          alt={item.filename || "Image"}
          className="w-full aspect-video object-cover"
        />
      )}
      {(item.type === "video" || item.type === "final_video") &&
        item.public_url && (
          <video
            src={item.public_url}
            controls
            className="w-full aspect-video object-cover"
          />
        )}
      {item.type === "voiceover" && item.public_url && (
        <div className="p-4 flex items-center gap-3">
          <svg
            className="w-8 h-8 text-purple-400 shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM21 16c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z"
            />
          </svg>
          <audio src={item.public_url} controls className="w-full h-8" />
        </div>
      )}
      {item.type === "script" && (
        <div className="p-4">
          <p className="text-sm text-gray-300 whitespace-pre-wrap line-clamp-6">
            {(item.metadata?.content as string) || "Script content"}
          </p>
        </div>
      )}

      {/* Labels */}
      <div className="px-3 py-2 flex items-center justify-between">
        <span className="text-xs text-gray-500">
          {item.scene_number ? `Scene ${item.scene_number}` : item.type.replace("_", " ")}
        </span>
        {item.public_url && (
          <a
            href={item.public_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="text-xs text-blue-400 hover:text-blue-300"
          >
            Open
          </a>
        )}
      </div>

      {/* Delete button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          if (confirmDelete) {
            onDelete();
            setConfirmDelete(false);
          } else {
            setConfirmDelete(true);
            setTimeout(() => setConfirmDelete(false), 3000);
          }
        }}
        className={`absolute top-2 right-2 w-6 h-6 rounded-full flex items-center justify-center text-xs transition opacity-0 group-hover:opacity-100 ${
          confirmDelete
            ? "bg-red-600 text-white opacity-100"
            : "bg-black/60 text-gray-300 hover:bg-red-600 hover:text-white"
        }`}
      >
        {confirmDelete ? "?" : "\u00D7"}
      </button>
    </div>
  );
}

export default function ProjectGallery({
  project,
  onBack,
  onDeleteProject,
  onMediaDeleted,
}: Props) {
  const [confirmDeleteProject, setConfirmDeleteProject] = useState(false);

  const handleDeleteMedia = async (mediaId: string) => {
    try {
      await deleteMediaItem(mediaId);
      onMediaDeleted(mediaId);
    } catch {
      // Silently fail — could add toast
    }
  };

  // Group media by type
  const images = project.media.filter((m) => m.type === "image").sort((a, b) => (a.scene_number || 0) - (b.scene_number || 0));
  const videos = project.media.filter((m) => m.type === "video").sort((a, b) => (a.scene_number || 0) - (b.scene_number || 0));
  const voiceover = project.media.find((m) => m.type === "voiceover");
  const finalVideo = project.media.find((m) => m.type === "final_video");
  const script = project.media.find((m) => m.type === "script");

  const date = new Date(project.created_at).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center text-gray-400 hover:text-white transition"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </button>
          <div>
            <h2 className="text-xl font-bold text-white">{project.name}</h2>
            <p className="text-sm text-gray-500">
              {date} &middot; {project.video_model} &middot; {project.status.replace("_", " ")}
            </p>
          </div>
        </div>
        <button
          onClick={() => {
            if (confirmDeleteProject) {
              onDeleteProject();
            } else {
              setConfirmDeleteProject(true);
              setTimeout(() => setConfirmDeleteProject(false), 3000);
            }
          }}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
            confirmDeleteProject
              ? "bg-red-600 text-white"
              : "bg-gray-800 text-gray-400 hover:text-red-400"
          }`}
        >
          {confirmDeleteProject ? "Confirm Delete?" : "Delete Project"}
        </button>
      </div>

      {/* Final Video */}
      {finalVideo && (
        <section className="mb-8">
          <h3 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">
            Final Video
          </h3>
          <div className="max-w-2xl">
            <MediaCard
              item={finalVideo}
              onDelete={() => handleDeleteMedia(finalVideo.id)}
            />
          </div>
        </section>
      )}

      {/* Script */}
      {script && (
        <section className="mb-8">
          <h3 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">
            Script
          </h3>
          <div className="max-w-2xl">
            <MediaCard
              item={script}
              onDelete={() => handleDeleteMedia(script.id)}
            />
          </div>
        </section>
      )}

      {/* Images */}
      {images.length > 0 && (
        <section className="mb-8">
          <h3 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">
            Images ({images.length})
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {images.map((item) => (
              <MediaCard
                key={item.id}
                item={item}
                onDelete={() => handleDeleteMedia(item.id)}
              />
            ))}
          </div>
        </section>
      )}

      {/* Videos */}
      {videos.length > 0 && (
        <section className="mb-8">
          <h3 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">
            Scene Videos ({videos.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {videos.map((item) => (
              <MediaCard
                key={item.id}
                item={item}
                onDelete={() => handleDeleteMedia(item.id)}
              />
            ))}
          </div>
        </section>
      )}

      {/* Voiceover */}
      {voiceover && (
        <section className="mb-8">
          <h3 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">
            Voiceover
          </h3>
          <div className="max-w-md">
            <MediaCard
              item={voiceover}
              onDelete={() => handleDeleteMedia(voiceover.id)}
            />
          </div>
        </section>
      )}

      {project.media.length === 0 && (
        <div className="text-center py-16 text-gray-500">
          <p>No media items in this project yet</p>
        </div>
      )}
    </div>
  );
}
