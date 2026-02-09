"use client";

import { useSession } from "@/hooks/useSession";
import TopicForm from "@/components/TopicForm";
import ChatView from "@/components/chat/ChatView";
import PipelineSidebar from "@/components/pipeline/PipelineSidebar";

export default function Home() {
  const {
    chatItems,
    currentProgress,
    awaiting,
    stage,
    isProcessing,
    error,
    pipelineStages,
    costTracking,
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
        <div className="flex">
          {/* Pipeline Sidebar */}
          <PipelineSidebar
            stages={pipelineStages}
            currentCost={costTracking.totalCost}
            budgetLimit={costTracking.budgetLimit}
          />

          {/* Main chat area */}
          <div className="flex-1 min-w-0">
            {/* New Project button */}
            <div className="flex justify-end px-6 py-2">
              <button
                type="button"
                onClick={reset}
                className="text-xs text-gray-500 hover:text-gray-300 transition"
              >
                New Project
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
          </div>
        </div>
      )}
    </>
  );
}
