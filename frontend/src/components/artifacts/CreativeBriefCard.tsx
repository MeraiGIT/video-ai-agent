"use client";
import { useState } from "react";

interface CreativeBrief {
  concept?: string;
  visual_style?: string;
  tone?: string;
  pacing?: string;
  audio_direction?: string;
  color_palette?: string;
  key_messages?: string[];
  reference_notes?: string;
}

interface Props {
  brief: CreativeBrief;
}

export default function CreativeBriefCard({ brief }: Props) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="mx-2 rounded-xl border border-purple-800/50 bg-gradient-to-br from-purple-900/20 to-blue-900/20 overflow-hidden">
      <div className="px-4 py-3 border-b border-purple-800/30 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-purple-400" />
          <span className="text-sm font-medium text-purple-300">Creative Brief</span>
        </div>
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-gray-400 hover:text-gray-300"
        >
          {expanded ? "Collapse" : "Expand"}
        </button>
      </div>

      <div className="px-4 py-3 space-y-3">
        {brief.concept && (
          <div>
            <span className="text-xs text-gray-400 uppercase tracking-wide">Concept</span>
            <p className="text-sm text-white mt-0.5">{brief.concept}</p>
          </div>
        )}

        {brief.visual_style && (
          <div>
            <span className="text-xs text-gray-400 uppercase tracking-wide">Visual Style</span>
            <p className="text-sm text-gray-300 mt-0.5">{brief.visual_style}</p>
          </div>
        )}

        {expanded && (
          <>
            {brief.tone && (
              <div>
                <span className="text-xs text-gray-400 uppercase tracking-wide">Tone</span>
                <p className="text-sm text-gray-300 mt-0.5">{brief.tone}</p>
              </div>
            )}

            {brief.pacing && (
              <div>
                <span className="text-xs text-gray-400 uppercase tracking-wide">Pacing</span>
                <p className="text-sm text-gray-300 mt-0.5">{brief.pacing}</p>
              </div>
            )}

            {brief.audio_direction && (
              <div>
                <span className="text-xs text-gray-400 uppercase tracking-wide">Audio</span>
                <p className="text-sm text-gray-300 mt-0.5">{brief.audio_direction}</p>
              </div>
            )}

            {brief.color_palette && (
              <div>
                <span className="text-xs text-gray-400 uppercase tracking-wide">Color Palette</span>
                <p className="text-sm text-gray-300 mt-0.5">{brief.color_palette}</p>
              </div>
            )}

            {brief.key_messages && brief.key_messages.length > 0 && (
              <div>
                <span className="text-xs text-gray-400 uppercase tracking-wide">Key Messages</span>
                <ul className="mt-1 space-y-1">
                  {brief.key_messages.map((msg, i) => (
                    <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                      <span className="text-purple-400 mt-0.5">&#8226;</span>
                      {msg}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {brief.reference_notes && (
              <div>
                <span className="text-xs text-gray-400 uppercase tracking-wide">References</span>
                <p className="text-sm text-gray-300 mt-0.5">{brief.reference_notes}</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
