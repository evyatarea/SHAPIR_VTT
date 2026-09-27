"""
Standalone smoke test - transcribe one audio file to Hebrew using a
local, open-source Whisper model (faster-whisper). No API key, no
cloud calls, no DB/AD/FastAPI required.

Setup:
    pip install faster-whisper

Usage:
    python scripts/transcribe_test_local.py path/to/recording.mp3 [model_size]

model_size options (bigger = more accurate, slower, more RAM):
    tiny, base, small (default), medium, large-v3
"""
import sys
from faster_whisper import WhisperModel


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/transcribe_test_local.py <audio_file> [model_size]")
        sys.exit(1)

    audio_path = sys.argv[1]
    model_size = sys.argv[2] if len(sys.argv) > 2 else "small"

    print(f"טוען מודל '{model_size}' (בפעם הראשונה זה מוריד את המשקולות, ייקח כמה דקות)...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, info = model.transcribe(audio_path, language="he")

    print(f"\n(שפה שזוהתה: {info.language}, ביטחון: {info.language_probability:.2f}, "
          f"משך: {info.duration:.1f} שניות)\n")
    print("=== תמלול ===\n")

    full_text = []
    for segment in segments:
        text = segment.text.strip()
        full_text.append(text)
        print(f"[{segment.start:6.1f}s -> {segment.end:6.1f}s] {text}")

    print("\n=== טקסט מלא ===\n")
    print(" ".join(full_text))


if __name__ == "__main__":
    main()
