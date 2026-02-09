"""Supabase persistence layer for project history.

All functions gracefully return None/empty when Supabase is not configured,
so the app works without it.
"""

import logging
from config import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    """Lazy-init Supabase client. Returns None if not configured."""
    global _client
    if _client is not None:
        return _client
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        return None
    try:
        from supabase import create_client

        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        return _client
    except Exception as e:
        logger.warning(f"Failed to init Supabase client: {e}")
        return None


def is_configured() -> bool:
    return _get_client() is not None


# ── Project CRUD ──────────────────────────────────────────────


def create_project(
    name: str,
    topic: str,
    content_type: str = "short_video",
    session_id: str | None = None,
    video_model: str = "",
    concat_enabled: bool = False,
) -> dict | None:
    """Create a new project record.

    Supports both legacy fields (video_model, concat_enabled) and
    new universal fields (content_type). session_id links to LangGraph thread.
    """
    client = _get_client()
    if not client:
        return None
    try:
        row = {
            "name": name,
            "topic": topic,
            "content_type": content_type,
        }
        if session_id:
            row["session_id"] = session_id
        # Include legacy fields if provided (for backwards compat)
        if video_model:
            row["video_model"] = video_model
        if concat_enabled:
            row["concat_enabled"] = concat_enabled
        result = client.table("projects").insert(row).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        return None


def update_project(project_id: str, updates: dict) -> dict | None:
    client = _get_client()
    if not client:
        return None
    try:
        result = (
            client.table("projects")
            .update(updates)
            .eq("id", project_id)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Failed to update project {project_id}: {e}")
        return None


def save_project_state(project_id: str, state: dict) -> dict | None:
    """Save the full project state snapshot (called at phase boundaries).

    Stores creative_brief, production_plan, blueprint, pipeline_stages,
    cost_breakdown as JSONB columns. These fields may not exist in the
    database table yet — if the columns don't exist, they're silently skipped.
    """
    updates: dict = {}

    # Map state fields to DB columns
    field_map = {
        "creative_brief": "creative_brief",
        "production_plan": "production_plan",
        "blueprint": "blueprint",
        "pipeline_stages": "pipeline_stages",
        "cost_breakdown": "cost_breakdown",
        "content_type": "content_type",
        "target_platform": "target_platform",
    }
    for state_key, db_key in field_map.items():
        val = state.get(state_key)
        if val is not None:
            updates[db_key] = val

    total_cost = state.get("total_cost")
    if total_cost is not None:
        updates["total_cost"] = total_cost

    status = state.get("status", "")
    if status:
        updates["status"] = status

    if not updates:
        return None

    return update_project(project_id, updates)


def get_project(project_id: str) -> dict | None:
    client = _get_client()
    if not client:
        return None
    try:
        result = (
            client.table("projects")
            .select("*, media(*)")
            .eq("id", project_id)
            .single()
            .execute()
        )
        return result.data
    except Exception as e:
        logger.error(f"Failed to get project {project_id}: {e}")
        return None


def list_projects() -> list[dict]:
    client = _get_client()
    if not client:
        return []
    try:
        result = (
            client.table("projects")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        return []


def delete_project(project_id: str) -> bool:
    """Delete project + cascade media records. Also removes files from Storage."""
    client = _get_client()
    if not client:
        return False
    try:
        # Get media records to find storage paths
        media_result = (
            client.table("media")
            .select("storage_path")
            .eq("project_id", project_id)
            .execute()
        )
        # Delete files from storage
        storage_paths = [
            m["storage_path"]
            for m in (media_result.data or [])
            if m.get("storage_path")
        ]
        if storage_paths:
            try:
                client.storage.from_("media").remove(storage_paths)
            except Exception as e:
                logger.warning(f"Failed to remove storage files: {e}")

        # Delete project (cascade deletes media records)
        client.table("projects").delete().eq("id", project_id).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to delete project {project_id}: {e}")
        return False


# ── Media CRUD ────────────────────────────────────────────────


def create_media_record(
    project_id: str,
    media_type: str,
    public_url: str | None = None,
    filename: str | None = None,
    storage_path: str | None = None,
    scene_number: int | None = None,
    stage: str | None = None,
    model_used: str | None = None,
    cost: float | None = None,
    metadata: dict | None = None,
) -> dict | None:
    """Create a media record with optional production tracking fields."""
    client = _get_client()
    if not client:
        return None
    try:
        row: dict = {
            "project_id": project_id,
            "type": media_type,
            "public_url": public_url,
            "filename": filename,
            "storage_path": storage_path,
        }
        if scene_number is not None:
            row["scene_number"] = scene_number
        if stage:
            row["stage"] = stage
        if model_used:
            row["model_used"] = model_used
        if cost is not None:
            row["cost"] = cost
        if metadata:
            row["metadata"] = metadata
        result = client.table("media").insert(row).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Failed to create media record: {e}")
        return None


def delete_media(media_id: str) -> bool:
    client = _get_client()
    if not client:
        return False
    try:
        # Get storage path before deleting
        result = (
            client.table("media")
            .select("storage_path")
            .eq("id", media_id)
            .single()
            .execute()
        )
        storage_path = result.data.get("storage_path") if result.data else None

        # Delete from storage
        if storage_path:
            try:
                client.storage.from_("media").remove([storage_path])
            except Exception as e:
                logger.warning(f"Failed to remove file from storage: {e}")

        # Delete DB record
        client.table("media").delete().eq("id", media_id).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to delete media {media_id}: {e}")
        return False


# ── File Upload ───────────────────────────────────────────────


def get_project_by_session(session_id: str) -> dict | None:
    """Look up a project by its session_id (LangGraph thread_id)."""
    client = _get_client()
    if not client:
        return None
    try:
        result = (
            client.table("projects")
            .select("*")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Failed to get project by session {session_id}: {e}")
        return None


# ── Chat Persistence ─────────────────────────────────────────


def save_chat_event(
    project_id: str,
    session_id: str,
    event_type: str,
    data: dict,
    ordinal: int = 0,
) -> dict | None:
    """Save a single SSE event to the chat_messages table."""
    client = _get_client()
    if not client:
        return None
    try:
        import json as _json

        # Ensure data is JSON-serializable (handle nested objects)
        serializable_data = _json.loads(_json.dumps(data, default=str))
        row = {
            "project_id": project_id,
            "session_id": session_id,
            "event_type": event_type,
            "data": serializable_data,
            "ordinal": ordinal,
        }
        result = client.table("chat_messages").insert(row).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Failed to save chat event: {e}")
        return None


def get_chat_history(project_id: str) -> list[dict]:
    """Get all chat events for a project, ordered by ordinal."""
    client = _get_client()
    if not client:
        return []
    try:
        result = (
            client.table("chat_messages")
            .select("*")
            .eq("project_id", project_id)
            .order("ordinal")
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to get chat history for {project_id}: {e}")
        return []


def delete_chat_history(project_id: str) -> bool:
    """Delete all chat messages for a project (cleanup on completion/abandon)."""
    client = _get_client()
    if not client:
        return False
    try:
        client.table("chat_messages").delete().eq("project_id", project_id).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to delete chat history for {project_id}: {e}")
        return False


# ── File Upload ───────────────────────────────────────────────


def upload_file(
    local_path: str, storage_path: str, content_type: str = "video/mp4"
) -> str | None:
    """Upload a local file to Supabase Storage and return the public URL."""
    client = _get_client()
    if not client:
        return None
    try:
        with open(local_path, "rb") as f:
            client.storage.from_("media").upload(
                storage_path,
                f,
                file_options={"content-type": content_type, "upsert": "true"},
            )
        public_url = client.storage.from_("media").get_public_url(storage_path)
        return public_url
    except Exception as e:
        logger.error(f"Failed to upload {local_path} to {storage_path}: {e}")
        return None
