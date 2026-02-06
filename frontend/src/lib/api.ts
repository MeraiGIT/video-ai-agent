const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function createSession(
  topic: string,
  videoModel: string,
  concatEnabled: boolean
): Promise<string> {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      topic,
      video_model: videoModel,
      concat_enabled: concatEnabled,
    }),
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

export function getMediaUrl(sessionId: string, filename: string): string {
  return `${API_BASE}/api/media/${sessionId}/${filename}`;
}

export function getEventStreamUrl(sessionId: string): string {
  return `${API_BASE}/api/sessions/${sessionId}/events`;
}
