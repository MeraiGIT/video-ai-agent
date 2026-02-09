"use client";
import { useState } from "react";

interface Scene {
  scene_number: number;
  narration?: string;
  visual_description?: string;
  image_prompt?: string;
  video_prompt?: string;
  camera?: { shot_type?: string; movement?: string; angle?: string };
  duration?: number;
  transition?: string;
  text_overlay?: string;
  sfx_cue?: string;
}

interface Blueprint {
  title?: string;
  summary?: string;
  scenes?: Scene[];
  audio_map?: {
    voiceover?: { full_script?: string; voice_direction?: string };
    music?: { style?: string; tempo?: string };
    sfx?: { cue: string; timestamp: number }[];
  };
  style_guide?: Record<string, unknown>;
  [key: string]: unknown;
}

interface Props {
  blueprint: Blueprint;
}

export default function BlueprintViewer({ blueprint }: Props) {
  const [expandedSection, setExpandedSection] = useState<string | null>("scenes");

  const scenes = blueprint.scenes || [];
  const audioMap = blueprint.audio_map;
  const styleGuide = blueprint.style_guide;

  // Collect "other" sections not covered by specialized renderers
  const knownKeys = new Set([
    "title", "summary", "scenes", "audio_map", "style_guide",
  ]);
  const otherSections = Object.entries(blueprint).filter(
    ([k]) => !knownKeys.has(k) && blueprint[k] !== null && blueprint[k] !== undefined,
  );

  const toggleSection = (name: string) => {
    setExpandedSection(expandedSection === name ? null : name);
  };

  return (
    <div className="mx-2 rounded-xl border border-indigo-800/50 bg-gradient-to-br from-indigo-900/20 to-slate-900/20 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-indigo-800/30 flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-indigo-400" />
        <span className="text-sm font-medium text-indigo-300">
          Blueprint: {blueprint.title || "Execution Plan"}
        </span>
      </div>

      {/* Summary */}
      {blueprint.summary && (
        <div className="px-4 py-2 border-b border-indigo-800/20">
          <p className="text-xs text-gray-400">{blueprint.summary}</p>
        </div>
      )}

      {/* Scenes */}
      {scenes.length > 0 && (
        <SectionToggle
          title={`Scenes (${scenes.length})`}
          expanded={expandedSection === "scenes"}
          onToggle={() => toggleSection("scenes")}
        >
          <div className="space-y-2">
            {scenes.map((scene, i) => (
              <div
                key={i}
                className="p-2 rounded-lg bg-gray-800/50 border border-gray-700/30"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 font-mono">
                    {scene.scene_number || i + 1}
                  </span>
                  {scene.duration && (
                    <span className="text-[10px] text-gray-500">
                      {scene.duration}s
                    </span>
                  )}
                  {scene.transition && (
                    <span className="text-[10px] text-gray-600">
                      → {scene.transition}
                    </span>
                  )}
                </div>
                {scene.narration && (
                  <p className="text-xs text-gray-300 mb-1">
                    <span className="text-gray-500">Script: </span>
                    {scene.narration}
                  </p>
                )}
                {scene.visual_description && (
                  <p className="text-[11px] text-gray-400">
                    <span className="text-gray-500">Visual: </span>
                    {scene.visual_description}
                  </p>
                )}
                {scene.camera && (
                  <p className="text-[10px] text-gray-500 mt-1">
                    Camera: {scene.camera.shot_type || ""} {scene.camera.movement || ""} {scene.camera.angle || ""}
                  </p>
                )}
                {scene.text_overlay && (
                  <p className="text-[10px] text-blue-400/70 mt-1">
                    Text: &quot;{scene.text_overlay}&quot;
                  </p>
                )}
              </div>
            ))}
          </div>
        </SectionToggle>
      )}

      {/* Audio Map */}
      {audioMap && (
        <SectionToggle
          title="Audio Map"
          expanded={expandedSection === "audio"}
          onToggle={() => toggleSection("audio")}
        >
          <div className="space-y-2">
            {audioMap.voiceover && (
              <div>
                <span className="text-[10px] text-gray-500 uppercase tracking-wide">
                  Voiceover
                </span>
                {audioMap.voiceover.voice_direction && (
                  <p className="text-xs text-gray-400">
                    Direction: {audioMap.voiceover.voice_direction}
                  </p>
                )}
                {audioMap.voiceover.full_script && (
                  <p className="text-xs text-gray-300 mt-1 p-2 bg-gray-800/50 rounded">
                    {audioMap.voiceover.full_script.length > 300
                      ? audioMap.voiceover.full_script.slice(0, 300) + "..."
                      : audioMap.voiceover.full_script}
                  </p>
                )}
              </div>
            )}
            {audioMap.music && (
              <div>
                <span className="text-[10px] text-gray-500 uppercase tracking-wide">
                  Music
                </span>
                <p className="text-xs text-gray-400">
                  {audioMap.music.style}
                  {audioMap.music.tempo && ` (${audioMap.music.tempo})`}
                </p>
              </div>
            )}
            {audioMap.sfx && audioMap.sfx.length > 0 && (
              <div>
                <span className="text-[10px] text-gray-500 uppercase tracking-wide">
                  SFX ({audioMap.sfx.length})
                </span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {audioMap.sfx.map((s, i) => (
                    <span
                      key={i}
                      className="text-[10px] px-1.5 py-0.5 rounded bg-gray-700/50 text-gray-400"
                    >
                      {s.cue} @{s.timestamp}s
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </SectionToggle>
      )}

      {/* Style Guide */}
      {styleGuide && (
        <SectionToggle
          title="Style Guide"
          expanded={expandedSection === "style"}
          onToggle={() => toggleSection("style")}
        >
          <pre className="text-[10px] text-gray-400 whitespace-pre-wrap overflow-x-auto">
            {JSON.stringify(styleGuide, null, 2)}
          </pre>
        </SectionToggle>
      )}

      {/* Other sections — rendered as collapsible JSON */}
      {otherSections.map(([key, value]) => (
        <SectionToggle
          key={key}
          title={key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
          expanded={expandedSection === key}
          onToggle={() => toggleSection(key)}
        >
          <pre className="text-[10px] text-gray-400 whitespace-pre-wrap overflow-x-auto max-h-48 overflow-y-auto">
            {typeof value === "string" ? value : JSON.stringify(value, null, 2)}
          </pre>
        </SectionToggle>
      ))}
    </div>
  );
}

function SectionToggle({
  title,
  expanded,
  onToggle,
  children,
}: {
  title: string;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="border-b border-indigo-800/20 last:border-b-0">
      <button
        type="button"
        onClick={onToggle}
        className="w-full px-4 py-2 flex items-center justify-between text-xs text-gray-400 hover:text-gray-300 transition-colors"
      >
        <span>{title}</span>
        <span className="text-gray-600">{expanded ? "−" : "+"}</span>
      </button>
      {expanded && <div className="px-4 pb-3">{children}</div>}
    </div>
  );
}
