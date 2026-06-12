import time
import bisect
import hashlib
from typing import List, Dict, Any, Tuple

class AlgorithmicQueryEngine:
    def __init__(self):
        # Optimized lookup structures
        self.count_index: Dict[Tuple[str, int], int] = {}
        self.exists_index: set[Tuple[str, str, int, str]] = set()
        self.latency_sorted: List[int] = []
        self.bytes_sorted: List[int] = []

    def preprocess(self, records: List[Dict[str, Any]]) -> float:
        """
        Indexes 50,000 records in a single linear pass. Target: <= 200ms.
        """
        start_time = time.perf_counter()
        
        latencies = []
        bytes_list = []

        for r in records:
            # 1. Populate Count Index
            count_key = (r.get("user_segment"), r.get("status_code"))
            self.count_index[count_key] = self.count_index.get(count_key, 0) + 1
            
            # 2. Populate Exists Index
            exists_key = (
                r.get("endpoint"),
                r.get("method"),
                r.get("status_code"),
                r.get("user_segment")
            )
            self.exists_index.add(exists_key)
            
            # 3. Collect range fields for sorting
            if "latency_ms" in r:
                latencies.append(r["latency_ms"])
            if "request_bytes" in r:
                bytes_list.append(r["request_bytes"])

        # 4. Sort arrays to enable O(log N) binary search
        self.latency_sorted = sorted(latencies)
        self.bytes_sorted = sorted(bytes_list)
        
        return (time.perf_counter() - start_time) * 1000

    def answer_query(self, q: Dict[str, Any]) -> int:
        """
        Resolves individual queries using high-performance indexing constraints.
        """
        op = q["op"]
        
        if op == "count":
            key = (q.get("user_segment"), q.get("status_code"))
            return self.count_index.get(key, 0)
            
        elif op == "exists":
            key = (
                q.get("endpoint"),
                q.get("method"),
                q.get("status_code"),
                q.get("user_segment")
            )
            return 1 if key in self.exists_index else 0
            
        elif op == "range_count":
            field = q["field"]
            low, high = q["min"], q["max"]
            
            arr = self.latency_sorted if field == "latency_ms" else self.bytes_sorted
            
            # Binary search bounds: [low, high] inclusive
            idx_start = bisect.bisect_left(arr, low)
            idx_end = bisect.bisect_right(arr, high)
            return idx_end - idx_start
            
        raise ValueError(f"Unknown operation payload variant: {op}")

    def execute_batch(self, queries: List[Dict[str, Any]]) -> Tuple[List[int], float]:
        """
        Processes 10,000 requests using targeted indexes.
        """
        start_time = time.perf_counter()
        answers = [self.answer_query(q) for q in queries]
        duration_ms = (time.perf_counter() - start_time) * 1000
        return answers, duration_ms

def compute_verification_hash(answers: List[int]) -> str:
    """
    Computes precise deterministic platform compliance verification token.
    """
    payload = ",".join(str(a) for a in answers)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
