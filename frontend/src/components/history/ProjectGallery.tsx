"use client";

import { useState } from "react";
import type { ProjectWithMedia, MediaItem } from "@/lib/api";
import { deleteMediaItem } from "@/lib/api";

interface Props {
  project: ProjectWithMedia;
  onBack: () => void;
  onDeleteProject: () => void;
  onContinue?: () => void;
  onAbandon?: () => void;
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
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">
            {item.scene_number != null ? `Scene ${item.scene_number + 1}` : item.type.replace("_", " ")}
          </span>
          {item.model_used && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-500">
              {item.model_used}
            </span>
          )}
          {item.cost != null && item.cost > 0 && (
            <span className="text-[10px] text-gray-600 font-mono">
              ${item.cost.toFixed(2)}
            </span>
          )}
        </div>
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
  onContinue,
  onAbandon,
  onMediaDeleted,
}: Props) {
  const [confirmDeleteProject, setConfirmDeleteProject] = useState(false);
  const [confirmAbandon, setConfirmAbandon] = useState(false);

  const handleDeleteMedia = async (mediaId: string) => {
    try {
      await deleteMediaItem(mediaId);
      onMediaDeleted(mediaId);
    } catch {
      // Silently fail
    }
  };

  // Group media by stage (pipeline-aware) — fallback to type for legacy projects
  const hasStages = project.media.some((m) => m.stage);
  const stageGroups: Record<string, MediaItem[]> = {};

  if (hasStages) {
    for (const item of project.media) {
      const key = item.stage || "Other";
      if (!stageGroups[key]) stageGroups[key] = [];
      stageGroups[key].push(item);
    }
    // Sort items within each stage by scene_number
    for (const items of Object.values(stageGroups)) {
      items.sort((a, b) => (a.scene_number || 0) - (b.scene_number || 0));
    }
  } else {
    // Legacy fallback: group by type
    for (const item of project.media) {
      const key = item.type || "Other";
      if (!stageGroups[key]) stageGroups[key] = [];
      stageGroups[key].push(item);
    }
    for (const items of Object.values(stageGroups)) {
      items.sort((a, b) => (a.scene_number || 0) - (b.scene_number || 0));
    }
  }

  const date = new Date(project.created_at).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  const statusColors: Record<string, string> = {
    completed: "text-green-400",
    in_progress: "text-blue-400",
    failed: "text-red-400",
    abandoned: "text-gray-400",
  };

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
              {date} &middot;{" "}
              {project.content_type?.replace("_", " ") || "project"} &middot;{" "}
              <span className={statusColors[project.status] || "text-gray-500"}>
                {project.status.replace("_", " ")}
              </span>
              {project.total_cost != null && project.total_cost > 0 && (
                <> &middot; ${project.total_cost.toFixed(2)}</>
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {onContinue && (
            <button
              onClick={onContinue}
              className="px-4 py-1.5 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white transition"
            >
              Continue
            </button>
          )}
          {onAbandon && (
            <button
              onClick={() => {
                if (confirmAbandon) {
                  onAbandon();
                  setConfirmAbandon(false);
                } else {
                  setConfirmAbandon(true);
                  setTimeout(() => setConfirmAbandon(false), 3000);
                }
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                confirmAbandon
                  ? "bg-orange-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:text-orange-400"
              }`}
            >
              {confirmAbandon ? "Confirm Abandon?" : "Abandon"}
            </button>
          )}
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
      </div>

      {/* Media grouped by pipeline stage */}
      {Object.entries(stageGroups).map(([stageName, items]) => (
        <section key={stageName} className="mb-8">
          <h3 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">
            {stageName.replace(/_/g, " ")} ({items.length})
          </h3>
          <div className={`grid gap-3 ${
            items.some((m) => m.type === "video" || m.type === "final_video")
              ? "grid-cols-1 md:grid-cols-2"
              : "grid-cols-2 md:grid-cols-3"
          }`}>
            {items.map((item) => (
              <MediaCard
                key={item.id}
                item={item}
                onDelete={() => handleDeleteMedia(item.id)}
              />
            ))}
          </div>
        </section>
      ))}

      {project.media.length === 0 && (
        <div className="text-center py-16 text-gray-500">
          <p>No media items in this project yet</p>
        </div>
      )}
    </div>
  );
}
