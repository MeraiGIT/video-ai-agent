const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function createSession(
  topic: string,
  uploadedFileUrls?: string[]
): Promise<string> {
  const body: Record<string, unknown> = {
    topic,
  };
  if (uploadedFileUrls && uploadedFileUrls.length > 0) {
    body.uploaded_file_urls = uploadedFileUrls;
  }

  const res = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Failed to create session: ${res.status}`);
  const data = await res.json();
  return data.session_id;
}

export async function resumeSession(
  sessionId: string,
  action: string,
  payload?: Record<string, unknown>
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/resume`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, payload }),
  });
  if (!res.ok) throw new Error(`Resume failed: ${res.status}`);
}

export async function uploadFile(
  sessionId: string,
  file: File
): Promise<{ file_url: string; file_type: string; filename: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}

export function getMediaUrl(sessionId: string, filename: string): string {
  return `${API_BASE}/api/media/${sessionId}/${filename}`;
}

export function getEventStreamUrl(sessionId: string): string {
  return `${API_BASE}/api/sessions/${sessionId}/events`;
}

// ── History API ──────────────────────────────────────────────

export interface Project {
  id: string;
  name: string;
  topic: string;
  content_type?: string;
  session_id?: string;
  video_model?: string;
  concat_enabled?: boolean;
  status: string;
  total_cost?: number;
  thumbnail_url: string | null;
  creative_brief?: Record<string, unknown>;
  production_plan?: Record<string, unknown>[];
  blueprint?: Record<string, unknown>;
  pipeline_stages?: Record<string, unknown>[];
  cost_breakdown?: Record<string, unknown>[];
  target_platform?: string;
  created_at: string;
  completed_at: string | null;
}

export interface MediaItem {
  id: string;
  project_id: string;
  type: string;
  storage_path: string | null;
  public_url: string | null;
  filename: string | null;
  scene_number: number | null;
  stage: string | null;
  model_used: string | null;
  cost: number | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ChatEvent {
  id: string;
  project_id: string;
  session_id: string;
  event_type: string;
  data: Record<string, unknown>;
  ordinal: number;
  created_at: string;
}

export interface ProjectWithMedia extends Project {
  media: MediaItem[];
}

export async function getProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE}/api/projects`);
  if (!res.ok) throw new Error(`Failed to fetch projects: ${res.status}`);
  const data = await res.json();
  return data.projects;
}

export async function getProject(projectId: string): Promise<ProjectWithMedia> {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}`);
  if (!res.ok) throw new Error(`Failed to fetch project: ${res.status}`);
  return res.json();
}

export async function deleteProject(projectId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to delete project: ${res.status}`);
}

export async function deleteMediaItem(mediaId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/media-items/${mediaId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to delete media: ${res.status}`);
}

// ── Resume / Chat / Abandon ──────────────────────────────────

export async function resumeProject(
  projectId: string
): Promise<{ session_id: string; status: string }> {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/resume`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Failed to resume project: ${res.status}`);
  return res.json();
}

export async function getProjectChat(
  projectId: string
): Promise<ChatEvent[]> {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/chat`);
  if (!res.ok) throw new Error(`Failed to get chat: ${res.status}`);
  const data = await res.json();
  return data.events;
}

export async function abandonProject(projectId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/abandon`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Failed to abandon project: ${res.status}`);
}
