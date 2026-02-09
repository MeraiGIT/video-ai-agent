"use client";

import { useState } from "react";
import type { Project } from "@/lib/api";

interface Props {
  project: Project;
  onClick: () => void;
  onDelete: () => void;
  onContinue?: () => void;
}

export default function ProjectCard({ project, onClick, onDelete, onContinue }: Props) {
  const [confirmDelete, setConfirmDelete] = useState(false);

  const statusColors: Record<string, string> = {
    completed: "bg-green-500/20 text-green-400",
    in_progress: "bg-blue-500/20 text-blue-400",
    failed: "bg-red-500/20 text-red-400",
    abandoned: "bg-gray-500/20 text-gray-400",
  };

  const date = new Date(project.created_at).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <div
      onClick={onClick}
      className="group relative rounded-xl border border-gray-800 bg-gray-900 hover:border-gray-700 transition-all cursor-pointer overflow-hidden"
    >
      {/* Thumbnail */}
      <div className="aspect-video bg-gray-800 relative">
        {project.thumbnail_url ? (
          <img
            src={project.thumbnail_url}
            alt={project.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <svg
              className="w-10 h-10 text-gray-700"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
          </div>
        )}
        {/* Status badge */}
        <span
          className={`absolute top-2 right-2 text-[10px] px-2 py-0.5 rounded-full font-medium ${
            statusColors[project.status] || statusColors.in_progress
          }`}
        >
          {project.status.replace("_", " ")}
        </span>
      </div>

      {/* Info */}
      <div className="p-3">
        <h3 className="text-sm font-medium text-white truncate">
          {project.name}
        </h3>
        <div className="flex items-center justify-between mt-1.5">
          <span className="text-xs text-gray-500">{date}</span>
          <div className="flex items-center gap-1.5">
            {project.content_type && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">
                {project.content_type.replace("_", " ")}
              </span>
            )}
            {project.total_cost != null && project.total_cost > 0 && (
              <span className="text-[10px] text-gray-600 font-mono">
                ${project.total_cost.toFixed(2)}
              </span>
            )}
          </div>
        </div>
        {/* Continue button for in-progress projects */}
        {project.status === "in_progress" && onContinue && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onContinue();
            }}
            className="mt-2 w-full py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition"
          >
            Continue
          </button>
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
        className={`absolute top-2 left-2 w-7 h-7 rounded-full flex items-center justify-center text-xs transition opacity-0 group-hover:opacity-100 ${
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
