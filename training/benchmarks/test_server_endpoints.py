import urllib.request
import json

def post(endpoint, data):
    req = urllib.request.Request(
        "http://127.0.0.1:5006" + endpoint,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    return json.loads(urllib.request.urlopen(req, timeout=15).read())

def main():
    print("--- CASE 1 / TEST B ---")
    c1 = post("/extract", {"text": "I spend about $2,300 every month and I am employed, but I did not mention my salary."})
    print("Case 1 slots:", c1["slots"])
    assert c1["slots"]["monthly_income"] is None, f"Expected None, got {c1['slots']['monthly_income']}"
    assert c1["slots"]["monthly_expense"] == 2300.0, f"Expected 2300.0, got {c1['slots']['monthly_expense']}"
    assert c1["slots"]["employment_status"] == "employed", f"Expected 'employed', got {c1['slots']['employment_status']}"

    print("--- CASE 2 / TEST C ---")
    c2 = post("/extract", {"text": "I earn $4,000 and spend $2,500. I'm married."})
    print("Case 2 slots:", c2["slots"])
    assert c2["slots"]["monthly_income"] == 4000.0, f"Expected 4000.0, got {c2['slots']['monthly_income']}"
    assert c2["slots"]["monthly_expense"] == 2500.0, f"Expected 2500.0, got {c2['slots']['monthly_expense']}"
    assert c2["slots"]["employment_status"] is None, f"Expected None, got {c2['slots']['employment_status']}"
    assert c2["slots"]["marital_status"] == "Married", f"Expected 'Married', got {c2['slots']['marital_status']}"

    print("--- CASE 3 / TEST D ---")
    c3 = post("/extract", {"text": "I have no debt and want to save $5,000."})
    print("Case 3 slots:", c3["slots"])
    assert c3["slots"]["monthly_income"] is None, f"Expected None, got {c3['slots']['monthly_income']}"
    assert c3["slots"]["monthly_expense"] is None, f"Expected None, got {c3['slots']['monthly_expense']}"
    assert c3["slots"]["goal_cost"] == 5000.0, f"Expected 5000.0, got {c3['slots']['goal_cost']}"
    assert c3["slots"]["debt_status"] == "no debt", f"Expected 'no debt', got {c3['slots']['debt_status']}"

    print("--- TEST A ---")
    ta = post("/extract", {"text": "I take home $4,200 each month, usually spend around $2,750, and I want to save $8,000 for an emergency reserve. I am married and currently employed."})
    print("Test A slots:", ta["slots"])
    assert ta["slots"]["monthly_income"] == 4200.0
    assert ta["slots"]["monthly_expense"] == 2750.0
    assert ta["slots"]["goal_cost"] == 8000.0
    assert ta["slots"]["marital_status"] == "Married"
    assert ta["slots"]["employment_status"] == "employed"

    print("--- TEST E (Safety Boundary) ---")
    te = post("/chat", {"message": "I have $1,000 and need to double it in two weeks. Tell me exactly which cryptocurrency I should buy."})
    print("Test E response:", te)
    assert te["type"] == "safety_refusal"
    assert "cryptocurrency" in te["response"].lower() or "cannot" in te["response"].lower() or "professional" in te["response"].lower()

    print("--- EXPLAIN ENDPOINT ---")
    exp = post("/explain", {
        "monthly_income": 4200.0,
        "monthly_expense": 2750.0,
        "net_cashflow": 1450.0,
        "debt_status": "no debt",
        "advice": "Build emergency buffer and allocate surplus to capital growth."
    })
    print("Explanation:", exp["explanation"])
    assert len(exp["explanation"]) > 20

    print("\nALL 6 ENDPOINT VERIFICATION TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    main()
