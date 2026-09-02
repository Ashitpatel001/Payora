import sys
import time
import requests

API_BASE = "http://localhost:8001/api"
API_KEY = "dev-secret-key"
HEADERS = {"x-api-key": API_KEY}

def run_evals():
    print("Starting batch evaluation...")
    res = requests.post(f"{API_BASE}/batch-run", headers=HEADERS)
    if not res.ok:
        print(f"Failed to start batch: {res.text}")
        sys.exit(1)
        
    run_id = res.json()["run_id"]
    print(f"Batch run triggered. ID: {run_id}")
    
    while True:
        res = requests.get(f"{API_BASE}/batch-results/{run_id}", headers=HEADERS)
        if not res.ok:
            print(f"Failed to fetch batch status: {res.text}")
            sys.exit(1)
            
        data = res.json()
        if data["status"] == "completed":
            break
        elif data["status"] == "failed":
            print("Batch run failed on server.")
            sys.exit(1)
            
        print("Waiting for batch completion...")
        time.sleep(2)
        
    print("\n--- Evaluation Results ---")
    print(f"Total Cases: {data['total_cases']}")
    print(f"Processed: {data['cases_processed']}")
    print(f"Recovery Rate: {data['recovery_rate']}%")
    print(f"Amount Recovered: {data['amount_recovered']} / {data['amount_at_risk']}")
    print(f"False Escalation Rate: {data['false_escalation_rate']}%")
    print("--------------------------")
    
    # Regression Gates
    MIN_RECOVERY_RATE = 20.0
    MAX_FALSE_ESCALATION = 5.0
    
    errors = []
    if data["recovery_rate"] < MIN_RECOVERY_RATE:
        errors.append(f"Recovery rate {data['recovery_rate']}% is below threshold {MIN_RECOVERY_RATE}%")
    if data["false_escalation_rate"] > MAX_FALSE_ESCALATION:
        errors.append(f"False escalation rate {data['false_escalation_rate']}% is above threshold {MAX_FALSE_ESCALATION}%")
        
    if errors:
        print("[FAIL] EVALUATION REGRESSION DETECTED")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("[PASS] EVALUATION PASSED")
        sys.exit(0)

if __name__ == "__main__":
    run_evals()