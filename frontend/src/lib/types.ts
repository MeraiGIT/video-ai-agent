export type VideoModel = "seedance" | "veo" | "kling" | "kling_ref";

export type SessionStage =
  | "topic_input"
  | "script_review"
  | "scenes_review"
  | "images_review"
  | "videos_review"
  | "voiceover_review"
  | "assembly"
  | "complete"
  | "error";

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
    | "individual_videos";
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

export interface UploadedFile {
  url: string;
  type: string;
  filename: string;
  preview?: string; // local object URL for preview
}

export const VIDEO_MODELS: {
  id: VideoModel;
  name: string;
  description: string;
  cost: string;
  provider: string;
}[] = [
  {
    id: "seedance",
    name: "Seedance 1.5 Pro",
    description: "ByteDance - Highest quality, natural motion",
    cost: "~$0.26/scene",
    provider: "fal.ai",
  },
  {
    id: "veo",
    name: "Google Veo 3.1 Fast",
    description: "Google DeepMind - Best value",
    cost: "~$0.10/scene",
    provider: "Kie AI",
  },
  {
    id: "kling",
    name: "Kling 2.6",
    description: "Kuaishou - Good quality, extended duration",
    cost: "~$0.15/scene",
    provider: "Kie AI",
  },
  {
    id: "kling_ref",
    name: "Kling O1 (Character Ref)",
    description: "Character consistency with reference images",
    cost: "~$0.56/scene",
    provider: "fal.ai",
  },
];
