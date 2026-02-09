"use client";

import { Suspense, useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { useSession } from "@/hooks/useSession";
import TopicForm from "@/components/TopicForm";
import ChatView from "@/components/chat/ChatView";
import PipelineSidebar from "@/components/pipeline/PipelineSidebar";

function HomeContent() {
  const searchParams = useSearchParams();
  const resumeProjectId = searchParams.get("resume");
  const resumeTriggered = useRef(false);

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
    resumeFromProject,
    reset,
  } = useSession();

  // Auto-resume if ?resume=projectId is in the URL
  useEffect(() => {
    if (resumeProjectId && !resumeTriggered.current) {
      resumeTriggered.current = true;
      resumeFromProject(resumeProjectId);
    }
  }, [resumeProjectId, resumeFromProject]);

  return (
    <>
      {stage === "topic_input" && !resumeProjectId ? (
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

export default function Home() {
  return (
    <Suspense>
      <HomeContent />
    </Suspense>
  );
}
