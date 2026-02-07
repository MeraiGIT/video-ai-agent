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
    <>
      {stage === "topic_input" ? (
        <TopicForm onSubmit={start} />
      ) : (
        <>
          {/* New Video button when in pipeline */}
          <div className="flex justify-end px-6 py-2">
            <button
              type="button"
              onClick={reset}
              className="text-xs text-gray-500 hover:text-gray-300 transition"
            >
              New Video
            </button>
          </div>
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
        </>
      )}
    </>
  );
}
