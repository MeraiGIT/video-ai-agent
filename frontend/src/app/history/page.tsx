"use client";

import { useState, useEffect, useCallback } from "react";
import type { Project, ProjectWithMedia } from "@/lib/api";
import { getProjects, getProject, deleteProject } from "@/lib/api";
import ProjectCard from "@/components/history/ProjectCard";
import ProjectGallery from "@/components/history/ProjectGallery";

export default function HistoryPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] =
    useState<ProjectWithMedia | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProjects = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getProjects();
      setProjects(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load projects");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const handleOpenProject = async (projectId: string) => {
    try {
      const data = await getProject(projectId);
      setSelectedProject(data);
    } catch {
      setError("Failed to load project details");
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    try {
      await deleteProject(projectId);
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
      if (selectedProject?.id === projectId) {
        setSelectedProject(null);
      }
    } catch {
      setError("Failed to delete project");
    }
  };

  const handleBack = () => {
    setSelectedProject(null);
    loadProjects();
  };

  if (selectedProject) {
    return (
      <ProjectGallery
        project={selectedProject}
        onBack={handleBack}
        onDeleteProject={() => handleDeleteProject(selectedProject.id)}
        onMediaDeleted={(mediaId) => {
          setSelectedProject((prev) =>
            prev
              ? { ...prev, media: prev.media.filter((m) => m.id !== mediaId) }
              : null
          );
        }}
      />
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-white">Generation History</h2>
          <p className="text-sm text-gray-400 mt-1">
            Browse your past video creations
          </p>
        </div>
      </div>

      {loading && (
        <div className="flex justify-center py-20">
          <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {error && (
        <div className="text-center py-20">
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={loadProjects}
            className="text-sm text-blue-400 hover:text-blue-300"
          >
            Try again
          </button>
        </div>
      )}

      {!loading && !error && projects.length === 0 && (
        <div className="text-center py-20">
          <div className="text-4xl mb-4">🎬</div>
          <p className="text-gray-400 mb-2">No projects yet</p>
          <p className="text-sm text-gray-500">
            Create your first video to see it here
          </p>
        </div>
      )}

      {!loading && projects.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onClick={() => handleOpenProject(project.id)}
              onDelete={() => handleDeleteProject(project.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
