"use client";
import { useRef, useEffect } from "react";
import type { ChatItem, ProgressUpdate, AwaitingState } from "@/lib/types";
import MessageBubble from "@/components/chat/MessageBubble";
import ScriptBlock from "@/components/artifacts/ScriptBlock";
import SceneCards from "@/components/artifacts/SceneCards";
import ImageGrid from "@/components/artifacts/ImageGrid";
import VideoGrid from "@/components/artifacts/VideoGrid";
import VoiceoverPlayer from "@/components/artifacts/VoiceoverPlayer";
import FinalVideo from "@/components/artifacts/FinalVideo";
import ProgressIndicator from "@/components/artifacts/ProgressIndicator";
import InputBar from "@/components/input/InputBar";

interface Props {
  chatItems: ChatItem[];
  currentProgress: ProgressUpdate | null;
  awaiting: AwaitingState | null;
  isProcessing: boolean;
  error: string | null;
  onApprove: () => void;
  onModify: (message: string) => void;
  onRegenerate: (indices: number[]) => void;
  onReset: () => void;
}

export default function ChatView({
  chatItems,
  currentProgress,
  awaiting,
  isProcessing,
  error,
  onApprove,
  onModify,
  onRegenerate,
  onReset,
}: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [chatItems, currentProgress]);

  const renderArtifact = (item: ChatItem & { kind: "artifact" }) => {
    const { type, data } = item.item;

    switch (type) {
      case "script":
        return (
          <ScriptBlock
            content={data.content as string}
            wordCount={data.word_count as number}
          />
        );

      case "scenes":
        return (
          <SceneCards
            scenes={data.scenes as { scene_number: number; narration: string; visual_description: string; image_prompt: string; duration: number }[]}
            totalDuration={data.total_duration as number}
          />
        );

      case "image": {
        // Collect all image artifacts up to this point to show full grid
        const allImages: { scene_index: number; url: string }[] = [];
        for (const ci of chatItems) {
          if (ci.kind === "artifact" && ci.item.type === "image") {
            allImages.push({
              scene_index: ci.item.data.scene_index as number,
              url: ci.item.data.url as string,
            });
          }
        }
        // Only render the grid on the last image artifact to avoid duplicates
        const lastImageItem = [...chatItems]
          .reverse()
          .find((ci) => ci.kind === "artifact" && ci.item.type === "image");
        if (lastImageItem && lastImageItem.kind === "artifact" && lastImageItem.item.id === item.item.id) {
          return (
            <ImageGrid
              images={allImages}
              totalScenes={data.total_scenes as number || allImages.length}
              onRegenerate={awaiting?.stage === "images_review" ? (i) => onRegenerate([i]) : undefined}
            />
          );
        }
        return null;
      }

      case "video": {
        const allVideos: { scene_index: number; url: string }[] = [];
        for (const ci of chatItems) {
          if (ci.kind === "artifact" && ci.item.type === "video") {
            allVideos.push({
              scene_index: ci.item.data.scene_index as number,
              url: ci.item.data.url as string,
            });
          }
        }
        const lastVideoItem = [...chatItems]
          .reverse()
          .find((ci) => ci.kind === "artifact" && ci.item.type === "video");
        if (lastVideoItem && lastVideoItem.kind === "artifact" && lastVideoItem.item.id === item.item.id) {
          return (
            <VideoGrid
              videos={allVideos}
              totalScenes={data.total_scenes as number || allVideos.length}
              onRegenerate={awaiting?.stage === "videos_review" ? (i) => onRegenerate([i]) : undefined}
            />
          );
        }
        return null;
      }

      case "voiceover":
        return (
          <VoiceoverPlayer
            url={data.url as string}
            duration={data.duration as number | undefined}
          />
        );

      case "final_video":
        return (
          <FinalVideo
            url={data.url as string}
            onCreateAnother={onReset}
          />
        );

      case "individual_videos":
        return (
          <FinalVideo
            urls={data.urls as string[]}
            onCreateAnother={onReset}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-72px)]">
      {/* Scrollable chat area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto chat-scroll px-4 py-4 space-y-4">
        {chatItems.map((item) => {
          if (item.kind === "message") {
            return <MessageBubble key={item.item.id} message={item.item} />;
          }
          const rendered = renderArtifact(item as ChatItem & { kind: "artifact" });
          if (!rendered) return null;
          return <div key={item.item.id}>{rendered}</div>;
        })}

        {currentProgress && <ProgressIndicator progress={currentProgress} />}

        {error && (
          <div className="mx-2 p-3 rounded-xl bg-red-900/30 border border-red-800">
            <p className="text-sm text-red-300">{error}</p>
            <button
              type="button"
              onClick={onReset}
              className="mt-2 text-xs text-red-400 hover:text-red-300 underline"
            >
              Start over
            </button>
          </div>
        )}
      </div>

      {/* Input bar */}
      <InputBar
        awaiting={awaiting}
        isProcessing={isProcessing}
        onApprove={onApprove}
        onModify={onModify}
        onRegenerate={onRegenerate}
      />
    </div>
  );
}
