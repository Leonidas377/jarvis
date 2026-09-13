import urllib.request
import json
import sys

def test_brief(query, mode="brief"):
    print("=" * 80)
    print(f"QUERY: {query} (Mode: {mode})")
    print("=" * 80)
    
    payload = json.dumps({
        "query": query,
        "answerMode": mode,
        "sourceCount": 4
    }).encode("utf-8")
    
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/research/brief",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
            print(f"TITLE: {data.get('title')}")
            print(f"MODE: {data.get('answerMode')} | TOPIC: {data.get('topicType')}")
            print(f"STATUS: {data.get('status')}")
            print("-" * 80)
            print("DIRECT ANSWER:")
            print(data.get("directAnswer"))
            print("-" * 80)
            print("RESEARCH BRIEF:")
            for i, p in enumerate(data.get("briefParagraphs", []), 1):
                print(f"{p}\n")
            
            key_points = data.get("keyPoints", [])
            if key_points:
                print("KEY POINTS:")
                for kp in key_points:
                    print(f" • {kp.get('text')} [Citations: {', '.join(kp.get('citationIds', []))}]")
                print("-" * 80)
                
            print(f"TAKEAWAY:\n{data.get('takeaway')}")
            print("-" * 80)
            
            citations = data.get("citations", [])
            print(f"COMPACT SOURCES ({len(citations)} verified sources):")
            for c in citations:
                print(f" [{c.get('id')}] {c.get('title')}")
                print(f"     Publisher: {c.get('publisher')} | Type: {c.get('sourceType')}")
                print(f"     URL: {c.get('url')}")
            
            limits = data.get("limitations", [])
            if limits:
                print("-" * 80)
                print(f"LIMITATIONS & UNCERTAINTIES:")
                for lim in limits:
                    print(f" - {lim}")
                    
            print("=" * 80)
            return data
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "What is quantum computing and why is it important?"
    m = sys.argv[2] if len(sys.argv) > 2 else "brief"
    test_brief(q, m)
