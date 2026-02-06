"use client";

import { useSession } from "@/hooks/useSession";
import TopicForm from "@/components/TopicForm";
import ChatView from "@/components/chat/ChatView";

export default function Home() {
  const {
    chatItems,
    currentProgress,
    awaiting,
    stage,
    isProcessing,
    error,
    start,
    approve,
    modify,
    regenerate,
    reset,
  } = useSession();

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <div className="h-[72px] flex items-center px-6 border-b border-gray-800/50">
        <h1 className="text-lg font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          AI Content Maker
        </h1>
        {stage !== "topic_input" && (
          <button
            type="button"
            onClick={reset}
            className="ml-auto text-xs text-gray-500 hover:text-gray-300 transition"
          >
            New Video
          </button>
        )}
      </div>

      {/* Content */}
      {stage === "topic_input" ? (
        <TopicForm onSubmit={start} />
      ) : (
        <ChatView
          chatItems={chatItems}
          currentProgress={currentProgress}
          awaiting={awaiting}
          isProcessing={isProcessing}
          error={error}
          onApprove={approve}
          onModify={modify}
          onRegenerate={regenerate}
          onReset={reset}
        />
      )}
    </div>
  );
}
