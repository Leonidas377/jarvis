import urllib.request
import json
import sys

def test_brief_and_followup():
    print("=" * 80)
    print("STAGE 1: GENERATE INITIAL BRIEF")
    print("=" * 80)
    
    payload = json.dumps({
        "query": "Compare RISC-V vs ARM architecture",
        "answerMode": "brief",
        "sourceCount": 3
    }).encode("utf-8")
    
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/research/brief",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    
    with urllib.request.urlopen(req, timeout=60) as resp:
        brief = json.loads(resp.read().decode("utf-8"))
        brief_id = brief["id"]
        print(f"Brief ID: {brief_id}")
        print(f"Direct Answer:\n{brief['directAnswer']}\n")
        print("Paragraphs:")
        for p in brief["briefParagraphs"]:
            print(f" • {p}")
        print(f"\nTakeaway: {brief['takeaway']}")
        print(f"Sources: {[c['title'] for c in brief['citations']]}\n")
        
    print("=" * 80)
    print("STAGE 2: TRIGGER FOLLOW-UP ACTION: 'simplify'")
    print("=" * 80)
    
    act_payload = json.dumps({"action": "simplify"}).encode("utf-8")
    act_req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/research/brief/{brief_id}/action",
        data=act_payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(act_req, timeout=60) as resp:
        simplified = json.loads(resp.read().decode("utf-8"))
        print(f"Mode: {simplified['answerMode']}")
        print(f"Direct Answer:\n{simplified['directAnswer']}\n")
        print("Paragraphs:")
        for p in simplified["briefParagraphs"]:
            print(f" • {p}")
        print(f"\nTakeaway: {simplified['takeaway']}")
        print(f"Sources Preserved: {[c['title'] for c in simplified['citations']]}\n")

    print("=" * 80)
    print("STAGE 3: TRIGGER FOLLOW-UP ACTION: 'more_detail'")
    print("=" * 80)
    act_payload2 = json.dumps({"action": "more_detail"}).encode("utf-8")
    act_req2 = urllib.request.Request(
        f"http://127.0.0.1:8000/api/research/brief/{brief_id}/action",
        data=act_payload2,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(act_req2, timeout=60) as resp:
        detailed = json.loads(resp.read().decode("utf-8"))
        print(f"Mode: {detailed['answerMode']}")
        print(f"Direct Answer:\n{detailed['directAnswer']}\n")
        print(f"Number of detailed paragraphs: {len(detailed['briefParagraphs'])}")
        for i, p in enumerate(detailed["briefParagraphs"], 1):
            print(f" [{i}] {p}")
        print(f"\nTakeaway: {detailed['takeaway']}")

if __name__ == "__main__":
    test_brief_and_followup()
