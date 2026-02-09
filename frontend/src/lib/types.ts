// === Session & Pipeline ===

export type SessionStage =
  | "topic_input"
  | "intake"
  | "interview"
  | "research"
  | "creative_direction"
  | "blueprint"
  | "producing"
  | "quality_gate"
  | "assembly"
  | "polish"
  | "deliver"
  | "complete"
  | "error";

export interface PipelineStage {
  name: string;
  status: "pending" | "active" | "completed" | "failed";
  cost?: number;
  assetsCount?: number;
  substeps?: { name: string; status: string }[];
}

// === Chat ===

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export interface ChatArtifact {
  id: string;
  type:
    | "script"
    | "scenes"
    | "image"
    | "video"
    | "voiceover"
    | "final_video"
    | "individual_videos"
    | "creative_brief"
    | "budget_variants"
    | "blueprint"
    | "quality_report"
    | "metadata"
    | "chunk_progress";
  data: Record<string, unknown>;
}

export interface ProgressUpdate {
  stage: string;
  current?: number;
  total?: number;
  message: string;
}

export interface AwaitingState {
  stage: string;
  actions: string[];
}

export type ChatItem =
  | { kind: "message"; item: ChatMessage }
  | { kind: "artifact"; item: ChatArtifact };

// === Files ===

export interface UploadedFile {
  url: string;
  type: string;
  filename: string;
  preview?: string;
}

// === Cost Tracking ===

export interface CostTracking {
  totalCost: number;
  budgetLimit: number;
  breakdown: { step: string; model: string; count: number; unitCost: number; total: number }[];
}

// === Creative Direction ===

export interface BudgetVariant {
  tier: "budget" | "standard" | "premium";
  totalEstimate: number;
  modelSelections: Record<string, string>;
  costBreakdown: {
    step: string;
    model: string;
    count: number;
    unitCost: number;
    total: number;
  }[];
  tradeoffs: string;
}

export interface CreativeBrief {
  summary: string;
  contentType: string;
  platform: string;
  audience: string;
  tone: string;
  style: string;
  keyMessages: string[];
}
