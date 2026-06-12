import os
import urllib.request
import json
from challenges.algorithm.solver import AlgorithmicQueryEngine, compute_verification_hash

# 1. Configuration
API_KEY = os.environ.get("API_KEY", "sa_614a45113a780a98c8a4d1a705f015ea20ff9611c68e3e3d3b1aad9ed878645b")
BASE_URL = os.environ.get("BASE_URL", "https://ca-seassessment-api-dev.happywater-190f264d.northcentralus.azurecontainerapps.io") # Change to your actual assessment host

headers = {"Authorization": f"Bearer {API_KEY}"}

# 2. Fetch the 50,000 Jumbo Records
# (Using the efficient bulk endpoint as hinted by OPTIONS /api/v1/dataset/jumbo)
print("Fetching the 50,000 jumbo records...")
dataset_req = urllib.request.Request(
    f"{BASE_URL}/api/v1/dataset/jumbo", 
    headers={"Authorization": f"Bearer {API_KEY}"},
    method="OPTIONS"
)
with urllib.request.urlopen(dataset_req) as r:
    dataset = json.load(r) # Expecting a list of 50,000 dictionaries

# 3. Fetch the 10,000 Queries
print("Fetching the 10,000 query batch...")
queries_req = urllib.request.Request(f"{BASE_URL}/api/v1/challenges/algorithm/queries", headers=headers)
with urllib.request.urlopen(queries_req) as r:
    batch = json.load(r)
queries = batch["queries"]

# 4. Initialize Engine & Preprocess Data
print("Initializing index engines...")
engine = AlgorithmicQueryEngine()
preprocess_time = engine.preprocess(dataset)
print(f"Preprocessing completed in {preprocess_time:.2f}ms")

# 5. Compute the 10,000 results
print("Executing batch queries...")
answers, batch_time = engine.execute_batch(queries)
print(f"Computed all {len(answers)} results in {batch_time:.2f}ms")

# 6. Generate the Verification Hash
final_hash = compute_verification_hash(answers)
print(f"\nYour 64-character SHA-256 Hash is:\n {final_hash}\n")

# 7. Print payload format ready for your POST /api/v1/submit
submission_payload = {
    "type": "algorithm_answer",
    "value": final_hash,
    "notes": f"Processed via O(N+K) engine. Preprocess: {preprocess_time:.1f}ms, Batch: {batch_time:.1f}ms"
}
print("Submission Payload:")
print(json.dumps(submission_payload, indent=2))