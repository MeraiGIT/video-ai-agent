export type VideoModel = "seedance" | "veo" | "kling";

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

export const VIDEO_MODELS: {
  id: VideoModel;
  name: string;
  description: string;
  cost: string;
}[] = [
  {
    id: "seedance",
    name: "Seedance 1.5 Pro",
    description: "ByteDance - Best value, natural motion",
    cost: "~$0.26/scene",
  },
  {
    id: "veo",
    name: "Google Veo 3.1",
    description: "Google DeepMind - Highest quality",
    cost: "~$0.25/scene",
  },
  {
    id: "kling",
    name: "Kling 3.0",
    description: "Kuaishou - Extended duration, native audio",
    cost: "~$0.30/scene",
  },
];
