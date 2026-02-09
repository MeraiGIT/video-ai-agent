"use client";
import { useState, useCallback, useRef, useEffect } from "react";
import type {
  ChatItem,
  ChatMessage,
  ChatArtifact,
  ProgressUpdate,
  AwaitingState,
  SessionStage,
  PipelineStage,
  CostTracking,
} from "@/lib/types";
import { createSession, resumeSession, getEventStreamUrl } from "@/lib/api";

let itemIdCounter = 0;
function nextId(): string {
  return `item-${++itemIdCounter}-${Date.now()}`;
}

export function useSession() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [chatItems, setChatItems] = useState<ChatItem[]>([]);
  const [currentProgress, setCurrentProgress] = useState<ProgressUpdate | null>(
    null
  );
  const [awaiting, setAwaiting] = useState<AwaitingState | null>(null);
  const [stage, setStage] = useState<SessionStage>("topic_input");
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pipelineStages, setPipelineStages] = useState<PipelineStage[]>([]);
  const [costTracking, setCostTracking] = useState<CostTracking>({
    totalCost: 0,
    budgetLimit: 0,
    breakdown: [],
  });
  const eventSourceRef = useRef<EventSource | null>(null);

  const addChatItem = useCallback((item: ChatItem) => {
    setChatItems((prev) => [...prev, item]);
  }, []);

  const connectSSE = useCallback(
    (sid: string) => {
      const es = new EventSource(getEventStreamUrl(sid));
      eventSourceRef.current = es;

      es.addEventListener("message", (e: MessageEvent) => {
        const data = JSON.parse(e.data);
        addChatItem({
          kind: "message",
          item: { id: nextId(), role: data.role, content: data.content },
        });
        setCurrentProgress(null);
      });

      es.addEventListener("artifact", (e: MessageEvent) => {
        const data = JSON.parse(e.data);
        addChatItem({
          kind: "artifact",
          item: { id: nextId(), type: data.type, data },
        });
        setCurrentProgress(null);
      });

      es.addEventListener("progress", (e: MessageEvent) => {
        const data: ProgressUpdate = JSON.parse(e.data);
        setCurrentProgress(data);
      });

      es.addEventListener("awaiting", (e: MessageEvent) => {
        const data: AwaitingState = JSON.parse(e.data);
        setAwaiting(data);
        setStage(data.stage as SessionStage);
        setIsProcessing(false);
        setCurrentProgress(null);
      });

      es.addEventListener("pipeline_update", (e: MessageEvent) => {
        const data = JSON.parse(e.data);
        if (Array.isArray(data.stages)) {
          setPipelineStages(data.stages as PipelineStage[]);
        }
      });

      es.addEventListener("cost_update", (e: MessageEvent) => {
        const data = JSON.parse(e.data);
        setCostTracking((prev) => ({
          totalCost: data.total_cost ?? prev.totalCost,
          budgetLimit: data.budget_limit ?? prev.budgetLimit,
          breakdown: data.breakdown ?? prev.breakdown,
        }));
      });

      es.addEventListener("quality_gate", (e: MessageEvent) => {
        const data = JSON.parse(e.data);
        addChatItem({
          kind: "artifact",
          item: { id: nextId(), type: "quality_report", data },
        });
      });

      es.addEventListener("error", (e: Event) => {
        if (e instanceof MessageEvent) {
          try {
            const data = JSON.parse(e.data);
            setError(data.message || "An error occurred");
          } catch {
            setError("Connection error");
          }
        }
        setIsProcessing(false);
      });

      es.addEventListener("complete", (e: MessageEvent) => {
        JSON.parse(e.data); // parse to validate
        setStage("complete");
        setIsProcessing(false);
        setCurrentProgress(null);
        setAwaiting(null);
      });
    },
    [addChatItem]
  );

  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  const start = useCallback(
    async (
      topic: string,
      uploadedFileUrls?: string[]
    ) => {
      setIsProcessing(true);
      setError(null);
      setChatItems([]);
      setAwaiting(null);
      setCurrentProgress(null);
      setPipelineStages([]);
      setCostTracking({ totalCost: 0, budgetLimit: 0, breakdown: [] });

      try {
        const sid = await createSession(topic, uploadedFileUrls);
        setSessionId(sid);
        connectSSE(sid);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to start");
        setIsProcessing(false);
      }
    },
    [connectSSE]
  );

  const approve = useCallback(async () => {
    if (!sessionId) return;
    setIsProcessing(true);
    setAwaiting(null);
    addChatItem({
      kind: "message",
      item: { id: nextId(), role: "user", content: "Looks good, continue!" },
    });
    await resumeSession(sessionId, "approve");
  }, [sessionId, addChatItem]);

  const modify = useCallback(
    async (message: string) => {
      if (!sessionId) return;
      setIsProcessing(true);
      setAwaiting(null);
      addChatItem({
        kind: "message",
        item: { id: nextId(), role: "user", content: message },
      });
      await resumeSession(sessionId, "modify", { message });
    },
    [sessionId, addChatItem]
  );

  const regenerate = useCallback(
    async (indices: number[]) => {
      if (!sessionId) return;
      setIsProcessing(true);
      setAwaiting(null);
      addChatItem({
        kind: "message",
        item: {
          id: nextId(),
          role: "user",
          content: `Regenerate scene${indices.length > 1 ? "s" : ""} ${indices.map((i) => i + 1).join(", ")}`,
        },
      });
      await resumeSession(sessionId, "regenerate", { indices });
    },
    [sessionId, addChatItem]
  );

  const selectBudget = useCallback(
    async (tier: string) => {
      if (!sessionId) return;
      setIsProcessing(true);
      setAwaiting(null);
      addChatItem({
        kind: "message",
        item: { id: nextId(), role: "user", content: `Selected ${tier} budget tier` },
      });
      await resumeSession(sessionId, "approve", { selected_tier: tier });
    },
    [sessionId, addChatItem]
  );

  const reset = useCallback(() => {
    eventSourceRef.current?.close();
    eventSourceRef.current = null;
    setSessionId(null);
    setChatItems([]);
    setCurrentProgress(null);
    setAwaiting(null);
    setStage("topic_input");
    setIsProcessing(false);
    setError(null);
    setPipelineStages([]);
    setCostTracking({ totalCost: 0, budgetLimit: 0, breakdown: [] });
  }, []);

  return {
    sessionId,
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
    selectBudget,
    reset,
  };
}
