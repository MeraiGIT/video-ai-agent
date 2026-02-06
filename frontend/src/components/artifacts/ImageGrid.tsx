"use client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ImageData {
  scene_index: number;
  url: string;
  regenerated?: boolean;
}

interface Props {
  images: ImageData[];
  totalScenes: number;
  onRegenerate?: (index: number) => void;
}

export default function ImageGrid({ images, totalScenes, onRegenerate }: Props) {
  // Build a map of scene_index -> latest image url
  const imageMap = new Map<number, string>();
  for (const img of images) {
    imageMap.set(img.scene_index, img.url);
  }

  return (
    <div className="animate-slide-up mx-2">
      <div className="flex items-center gap-2 px-1 mb-2">
        <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
        <span className="text-xs font-medium text-gray-300 uppercase tracking-wider">
          Generated Images
        </span>
        <span className="ml-auto text-xs text-gray-500">
          {imageMap.size} / {totalScenes}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {Array.from({ length: totalScenes }, (_, i) => {
          const url = imageMap.get(i);
          return (
            <div key={i} className="relative group rounded-xl overflow-hidden border border-gray-700 bg-gray-900 aspect-video">
              {url ? (
                <>
                  <img
                    src={`${API_BASE}${url}`}
                    alt={`Scene ${i + 1}`}
                    className="w-full h-full object-cover transition-transform group-hover:scale-105"
                  />
                  {/* Scene label overlay */}
                  <div className="absolute top-1.5 left-1.5 px-1.5 py-0.5 rounded bg-black/60 text-[10px] text-white font-medium">
                    Scene {i + 1}
                  </div>
                  {/* Regenerate button */}
                  {onRegenerate && (
                    <button
                      type="button"
                      onClick={() => onRegenerate(i)}
                      className="absolute top-1.5 right-1.5 w-6 h-6 rounded-full bg-black/60 text-white opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center hover:bg-red-500/80"
                      title="Regenerate this image"
                    >
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </button>
                  )}
                </>
              ) : (
                <div className="w-full h-full skeleton-pulse flex items-center justify-center">
                  <span className="text-xs text-gray-600">Scene {i + 1}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
