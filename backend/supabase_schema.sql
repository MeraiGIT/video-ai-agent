-- Supabase Schema for AI Production Studio
-- Run this in your Supabase SQL Editor to set up the required tables.
-- Supabase is OPTIONAL — the app works without it (history/persistence disabled).

-- ── Projects table ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS projects (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    topic TEXT NOT NULL DEFAULT '',
    content_type TEXT NOT NULL DEFAULT 'short_video',

    -- Legacy v1 fields (kept for backwards compatibility)
    video_model TEXT DEFAULT '',
    concat_enabled BOOLEAN DEFAULT FALSE,

    -- v3 universal fields
    creative_brief JSONB,
    production_plan JSONB,
    blueprint JSONB,
    pipeline_stages JSONB,
    cost_breakdown JSONB,
    target_platform TEXT,
    total_cost NUMERIC DEFAULT 0,

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'in_progress',
    thumbnail_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- ── Media table ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS media (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    storage_path TEXT,
    public_url TEXT,
    filename TEXT,
    scene_number INTEGER,

    -- v3 production tracking fields
    stage TEXT,
    model_used TEXT,
    cost NUMERIC,

    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ── Indexes ─────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_media_project_id ON media(project_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at DESC);

-- ── Storage bucket ──────────────────────────────────────────────
-- Create a "media" bucket in Supabase Storage (public access for CDN URLs).
-- This is done via the Supabase dashboard or:
--   INSERT INTO storage.buckets (id, name, public) VALUES ('media', 'media', true);

-- ── Row Level Security (optional) ───────────────────────────────
-- Enable RLS if you want to restrict access. For a single-user app,
-- you can leave RLS disabled and use the service_role key.

-- ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE media ENABLE ROW LEVEL SECURITY;
