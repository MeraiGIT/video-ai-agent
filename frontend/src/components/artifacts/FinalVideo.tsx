"use client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Props {
  url?: string;
  urls?: string[];
  onCreateAnother: () => void;
}

export default function FinalVideo({ url, urls, onCreateAnother }: Props) {
  const download = (videoUrl: string, filename: string) => {
    const a = document.createElement("a");
    a.href = `${API_BASE}${videoUrl}`;
    a.download = filename;
    a.click();
  };

  return (
    <div className="animate-slide-up mx-2 space-y-3">
      <div className="flex items-center gap-2 px-1">
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
        <span className="text-xs font-medium text-gray-300 uppercase tracking-wider">
          Final Output
        </span>
      </div>

      {/* Single assembled video */}
      {url && (
        <div className="rounded-xl border border-gray-700 bg-gray-900 overflow-hidden">
          <video
            src={`${API_BASE}${url}`}
            className="w-full aspect-video"
            controls
            playsInline
          />
          <div className="flex items-center gap-2 p-3 border-t border-gray-700/50">
            <button
              type="button"
              onClick={() => download(url, "final-video.mp4")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 transition text-sm font-medium"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download
            </button>
            <button
              type="button"
              onClick={onCreateAnother}
              className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 transition text-sm"
            >
              Create Another
            </button>
          </div>
        </div>
      )}

      {/* Individual scene videos */}
      {urls && urls.length > 0 && (
        <div className="space-y-2">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {urls.map((vidUrl, i) => (
              <div key={i} className="rounded-xl border border-gray-700 bg-gray-900 overflow-hidden">
                <video
                  src={`${API_BASE}${vidUrl}`}
                  className="w-full aspect-video"
                  controls
                  playsInline
                />
                <div className="p-2 border-t border-gray-700/50 flex items-center justify-between">
                  <span className="text-xs text-gray-400">Scene {i + 1}</span>
                  <button
                    type="button"
                    onClick={() => download(vidUrl, `scene-${i + 1}.mp4`)}
                    className="text-xs text-emerald-400 hover:text-emerald-300 transition"
                  >
                    Download
                  </button>
                </div>
              </div>
            ))}
          </div>
          <div className="flex justify-end pt-1">
            <button
              type="button"
              onClick={onCreateAnother}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 transition text-sm"
            >
              Create Another
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
