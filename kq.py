"""kq.py - Test the Knowledge RAG API (upload + search).

Usage:
  python kq.py upload                         # upload the sample PDF payload
  python kq.py search "your question here"    # search against ingested knowledge
  python kq.py search                         # interactive search loop

Needs: nothing to install beyond Python stdlib.
"""
import json
import sys
import urllib.error
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_URL    = "http://localhost:8000/api/rag"
UPLOAD_URL  = f"{BASE_URL}/knowledge/"
SEARCH_URL  = f"{BASE_URL}/knowledge/search/"

TOP_K      = 3
THRESHOLD  = 0.25
WEIGHTS    = None   # None = server defaults, or e.g. {"question": 0.6, "summary": 0.4}
BAR_WIDTH  = 20
METADATA_ORDER = ["keyword", "question", "topic", "summary"]

# ─── Sample payload (PDF with 3 segments) ────────────────────────────────────
SAMPLE_PAYLOAD = {
    "title": "Corporate Code of Conduct and Compliance Handbook",
    "description": "Annual compliance document covering ethical behavior, anti-bribery regulations, and whistleblower protections.",
    "source_type": "pdf",
    "sources": [
        {"language": "en", "file_data": "JVBERi0xLjQKJcTl8uXrp/Og0MTGCjQgMCBvYmo=", "page_count": 24},
        {"language": "km", "file_data": "JVBERi0xLjQKJcTl8uXrp/Og0MTGCjQgMCBvYmo=", "page_count": 26},
    ],
    "segments": [
        {
            "segment_index": 0,
            "title": "Equal Opportunity & Anti-Harassment Policy",
            "summary": "Mandates a respectful work environment prohibiting harassment, discrimination, or retaliation based on gender, race, or religion.",
            "transcript": "Chapter 1: Workplace Respect. Our company is committed to maintaining a diverse, safe, and inclusive work culture.",
            "page_start": 1, "page_end": 4,
            "keywords": ["harassment", "discrimination", "diversity", "workplace respect", "equal opportunity"],
            "possible_questions": [
                "What is the company policy on workplace harassment?",
                "How does the company handle discriminatory complaints?",
            ],
        },
        {
            "segment_index": 1,
            "title": "Gift and Entertainment Policy",
            "summary": "Sets monetary gift limits ($50 max) and reporting procedures to avoid conflicts of interest with vendors and clients.",
            "transcript": "Chapter 2: Conflicts of Interest and Gifts. Employees may not accept gifts valued above $50.",
            "page_start": 5, "page_end": 8,
            "keywords": ["gifts", "bribery", "conflict of interest", "vendor entertainment", "compliance threshold"],
            "possible_questions": [
                "Can I accept a gift from a vendor or client?",
                "What is the maximum allowed gift value before reporting?",
            ],
        },
        {
            "segment_index": 2,
            "title": "Whistleblower Protection and Reporting Channels",
            "summary": "Explains confidential reporting channels, anonymous hotlines, and non-retaliation guarantees for whistleblowers.",
            "transcript": "Chapter 3: Speaking Up. If you suspect unethical behavior, you are protected under our non-retaliation policy.",
            "page_start": 9, "page_end": 14,
            "keywords": ["whistleblower", "anonymous hotline", "non-retaliation", "ethics reporting"],
            "possible_questions": [
                "How can I report a compliance violation anonymously?",
                "Am I protected from retaliation if I report misconduct?",
            ],
        },
    ],
}


# ─── HTTP helpers ─────────────────────────────────────────────────────────────

def _post(url, payload):
    body = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ─── Upload ───────────────────────────────────────────────────────────────────

def cmd_upload():
    print("Uploading sample knowledge payload …")
    try:
        result = _post(UPLOAD_URL, SAMPLE_PAYLOAD)
        print("\n✅ Upload successful!")
        print(f"   ID             : {result['id']}")
        print(f"   Title          : {result['title']}")
        print(f"   Source type    : {result['source_type']}")
        print(f"   Status         : {result['processing_status']}")
        print(f"   Segments saved : {result['segments_count']}")
        print(f"   Created at     : {result['created_at']}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"\n❌ HTTP {e.code}: {body}")
    except urllib.error.URLError as e:
        print(f"\n❌ Cannot reach API ({e}). Is 'docker compose up' running?")


# ─── Search display ───────────────────────────────────────────────────────────

def _bar(percent):
    filled = round(BAR_WIDTH * percent / 100)
    return "█" * filled + "░" * (BAR_WIDTH - filled)


def _show_confidence(result, weights):
    by_type = result.get("confidence_by_type", {})
    best    = result.get("best_match", "")
    print("   Confidence by metadata type:")
    for name in METADATA_ORDER:
        if name not in by_type:
            print(f"     {name:<9} (no data)")
            continue
        pct    = by_type[name]
        wt_str = f"weight {weights.get(name, 0):.2f}" if weights else ""
        mark   = "  <- best match" if name == best else ""
        print(f"     {name:<9} {_bar(pct)} {pct:6.2f}%   {wt_str}{mark}")


def _show(data):
    results = data.get("results", [])
    if not results:
        print("\n  No matching segments found.\n")
        return

    weights = data.get("weights_used", {})
    print(f"\nFound {data['count']} matching segment(s) "
          f"[language: {data.get('language', 'en')}]:\n")

    for i, r in enumerate(results, start=1):
        print(f"{i}. [{r['source_type']}]  {r['knowledge_title']}")
        print(f"   Segment #{r['segment_index']}: {r['title'] or '(untitled)'}")
        if r.get("page_start") is not None:
            print(f"   Pages    : {r['page_start']} – {r['page_end']}")
        if r.get("start_time_seconds") is not None:
            print(f"   Time     : {r['start_time_seconds']}s – {r['end_time_seconds']}s")
        print(f"   Summary  : {r['summary']}")
        print(f"   SCORE    : {r['score']:.4f}   CONFIDENCE: {r['confidence']:.2f}%")
        _show_confidence(r, weights)

        src = r.get("matched_source")
        if src:
            fallback = " (fallback)" if src.get("is_fallback") else ""
            print(f"   Source   : language={src['language']}{fallback}  "
                  f"pages={src.get('page_count')}  "
                  f"duration={src.get('duration_seconds')}s")
        print()

    print("─── RAW JSON (first result) ───")
    print(json.dumps(results[0], indent=2, ensure_ascii=False))
    print()


def cmd_search(question=None, language="en"):
    payload = {"question": question, "top_k": TOP_K, "threshold": THRESHOLD, "language": language}
    if WEIGHTS:
        payload["weights"] = WEIGHTS
    try:
        _show(_post(SEARCH_URL, payload))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"\n❌ HTTP {e.code}: {body}")
    except urllib.error.URLError as e:
        print(f"\n❌ Cannot reach API ({e}). Is 'docker compose up' running?")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def cmd_search_loop():
    print("Knowledge Search  (type 'q' to quit)")
    while True:
        question = input("\nYour question: ").strip()
        if question.lower() in ("q", "quit", "exit"):
            break
        if not question:
            continue
        cmd_search(question)


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if not args or args[0] == "upload":
        cmd_upload()

    elif args[0] == "search":
        if len(args) > 1:
            cmd_search(" ".join(args[1:]))
        else:
            cmd_search_loop()

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
