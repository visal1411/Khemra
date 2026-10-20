"""Ask questions to the video-segment search API.

Run:   python ask.py
Needs: nothing to install (uses only the Python standard library).

For every matching segment it shows:
  - the combined confidence (all metadata merged by weight)
  - the confidence of EACH metadata type (keyword / question / topic / summary)
  - which metadata matched best
"""
import json
import urllib.error
import urllib.request

API_URL = "http://localhost:8000/api/rag/search/"
TOP_K = 1         # how many segments to return
THRESHOLD = 0.30   # ignore segments whose combined score is lower than this
WEIGHTS = None     # None = server defaults, or e.g. {"question": 0.6, "summary": 0.4}

METADATA_ORDER = ["keyword", "question", "topic", "summary"]
BAR_WIDTH = 20


def search(question):
    payload = {"question": question, "top_k": TOP_K, "threshold": THRESHOLD}
    if WEIGHTS:
        payload["weights"] = WEIGHTS
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def bar(percent):
    filled = round(BAR_WIDTH * percent / 100)
    return "█" * filled + "░" * (BAR_WIDTH - filled)


def show_confidence(result, weights):
    by_type = result.get("confidence_by_type", {})
    best = result.get("best_match")
    print("   Confidence by metadata:")
    for name in METADATA_ORDER:
        if name not in by_type:
            print(f"     {name:<9} (no data)")
            continue
        pct = by_type[name]
        weight = f"weight {weights.get(name, 0):.2f}" if weights else ""
        mark = "  <- best match" if name == best else ""
        print(f"     {name:<9} {bar(pct)} {pct:6.2f}%   {weight}{mark}")


# def show(data):
#     results = data["results"]
#     if not results:
#         print("\nNo matching video segment found.\n")
#         return
#     weights = data.get("weights", {})
#     print(f"\nFound {data['count']} matching segment(s):\n")
#     for i, r in enumerate(results, start=1):
#         print(f"{i}. {r['title']}")
#         print(f"   Segment: {r['segment_id']}")
#         print(f"   Video:   {r['video_id']}")
#         print(f"   Time:    {r['time']}")
#         print(f"   Summary: {r['summary']}")
#         print(f"   COMBINED CONFIDENCE: {r['confidence']:.2f}%   (score: {r['score']:.3f})")
#         show_confidence(r, weights)
#         print()

def show(data):
    results = data["results"]
    if not results:
        print("\nNo matching video segment found.\n")
        return

    weights = data.get("weights", {})
    print(f"\nFound {data['count']} matching segment(s):\n")
    for i, r in enumerate(results, start=1):
        print(f"{i}. {r['title']}")
        print(f"   Segment: {r['segment_id']}")
        print(f"   Video:   {r['video_id']}")
        print(f"   Time:    {r['time']}")
        print(f"   Summary: {r['summary']}")
        print(f"   COMBINED CONFIDENCE: {r['confidence']:.2f}%   (score: {r['score']:.3f})")
        show_confidence(r, weights)
        print()

    # --- RAW JSON (single object, no count/weights, no list) ---
    print("--- RAW JSON ---")
    print(json.dumps(results[0], indent=2, ensure_ascii=False))
    print()


def main():
    print("Video Segment Search  (type 'q' to quit)")
    while True:
        question = input("\nYour question: ").strip()
        if question.lower() in ("q", "quit", "exit"):
            break
        if not question:
            continue
        try:
            show(search(question))
        except urllib.error.URLError as e:
            print(f"\nCannot reach the API ({e}). Is 'docker compose up' running?")
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()