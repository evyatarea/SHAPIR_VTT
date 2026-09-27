"""
Standalone smoke test - transcribe one audio file to Hebrew with Whisper.
No DB, no AD, no FastAPI required - just an OpenAI API key.

Usage:
    export OPENAI_API_KEY=sk-...
    python scripts/transcribe_test.py path/to/recording.mp3
"""
import sys
from openai import OpenAI


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/transcribe_test.py <audio_file>")
        sys.exit(1)

    audio_path = sys.argv[1]
    client = OpenAI()  # reads OPENAI_API_KEY from environment

    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="he",
            response_format="verbose_json",
        )

    print("\n=== תמלול ===\n")
    print(result.text)
    print(f"\n(שפה שזוהתה: {getattr(result, 'language', 'he')}, "
          f"משך: {getattr(result, 'duration', '?')} שניות)")


if __name__ == "__main__":
    main()
