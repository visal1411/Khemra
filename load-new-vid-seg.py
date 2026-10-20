"""Insert a NEW video's segments (backend vectorizes & stores them).

Run:   python ask.py
Needs: nothing to install (uses only the Python standard library).
"""
import json
import time
import urllib.error
import urllib.request

SEGMENTS_URL = "http://localhost:8000/api/rag/segments/"


def post(url, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


def add_segment(seg):
    try:
        post(SEGMENTS_URL, seg)
        print(f"Saved: {seg['segment_id']}")
    except urllib.error.HTTPError as e:
        print(f"Failed {seg['segment_id']} -> {e.code}: {e.read().decode()}")
    except Exception as e:
        print(f"Failed {seg['segment_id']} -> {e}")


def input_segment(video_id, index):
    print(f"\n--- Segment {index} of video {video_id} ---")
    time_     = input("Time       (e.g. 00:00 - 00:09): ").strip()
    title     = input("Title      : ").strip()
    summary   = input("Summary    : ").strip()
    keywords  = input("Keywords   (comma separated): ").strip()
    questions = input("Questions  (comma separated): ").strip()

    return {
        "video_id": video_id,
        "segment_id": f"SEG-{video_id.split('-')[-1]}-{index:02d}",
        "time": time_,
        "title": title,
        "summary": summary,
        "keywords": [k.strip() for k in keywords.split(",") if k.strip()],
        "possible_questions": [q.strip() for q in questions.split("?") if q.strip()],
    }


def main():
    video_id = input("Video ID (press Enter to auto-generate): ").strip()
    if not video_id:
        video_id = f"VID-{int(time.time())}"
        print(f"Using video_id = {video_id}")

    print("\nAdd segments (they will be vectorized by the backend).")
    index = 1
    while True:
        add_segment(input_segment(video_id, index))
        index += 1
        if input("\nAdd another segment? (y/n): ").strip().lower() != "y":
            break

    print("\nDone.")


if __name__ == "__main__":
    main()