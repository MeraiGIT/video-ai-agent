def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_srt(segments, output_path: str):
    """Write faster-whisper segments to an SRT file.

    Groups words into ~5-word chunks for readable subtitles.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        index = 1
        for segment in segments:
            words = list(segment.words) if segment.words else []
            if not words:
                # Fallback: use segment-level timing
                f.write(f"{index}\n")
                f.write(
                    f"{format_timestamp(segment.start)} --> "
                    f"{format_timestamp(segment.end)}\n"
                )
                f.write(f"{segment.text.strip()}\n\n")
                index += 1
                continue

            chunk_size = 5
            for i in range(0, len(words), chunk_size):
                chunk = words[i : i + chunk_size]
                start = chunk[0].start
                end = chunk[-1].end
                text = " ".join(w.word.strip() for w in chunk)
                f.write(f"{index}\n")
                f.write(
                    f"{format_timestamp(start)} --> {format_timestamp(end)}\n"
                )
                f.write(f"{text}\n\n")
                index += 1
