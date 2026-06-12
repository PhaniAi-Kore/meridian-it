import time
import json
import hashlib
from typing import List, Dict, Any, Tuple

class AlgorithmicQueryEngine:
    def __init__(self):
        self.count_index: Dict[Tuple[str, int], int] = {}
        self.exists_index: set[Tuple[str, str, int, str]] = set()
        self.latency_sorted: List[int] = []
        self.bytes_sorted: List[int] = []

    def preprocess(self, records: List[Any]) -> float:
        """
        Defensively typecasts values to guarantee true exact matches.
        """
        start_time = time.perf_counter()
        
        latencies = []
        bytes_list = []

        for item in records:
            if isinstance(item, str):
                try:
                    r = json.loads(item)
                except json.JSONDecodeError:
                    continue
            else:
                r = item

            # Defensive parsing: ensure numerical types match query criteria
            try:
                status_code = int(r.get("status_code")) if r.get("status_code") is not None else None
            except (ValueError, TypeError):
                status_code = r.get("status_code")

            user_segment = str(r.get("user_segment")) if r.get("user_segment") is not None else None
            endpoint = str(r.get("endpoint")) if r.get("endpoint") is not None else None
            method = str(r.get("method")) if r.get("method") is not None else None

            # 1. Populate Count Index
            if user_segment is not None and status_code is not None:
                count_key = (user_segment, status_code)
                self.count_index[count_key] = self.count_index.get(count_key, 0) + 1
            
            # 2. Populate Exists Index
            if all(v is not None for v in [endpoint, method, status_code, user_segment]):
                exists_key = (endpoint, method, status_code, user_segment)
                self.exists_index.add(exists_key)
            
            # 3. Collect range fields safely
            if "latency_ms" in r and r["latency_ms"] is not None:
                try:
                    latencies.append(int(r["latency_ms"]))
                except (ValueError, TypeError):
                    pass
            if "request_bytes" in r and r["request_bytes"] is not None:
                try:
                    bytes_list.append(int(r["request_bytes"]))
                except (ValueError, TypeError):
                    pass

        # 4. Sort arrays for quick lookup calculations
        self.latency_sorted = sorted(latencies)
        self.bytes_sorted = sorted(bytes_list)
        
        return (time.perf_counter() - start_time) * 1000

    def answer_query(self, q: Dict[str, Any]) -> int:
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
            
            # Native manual index slicing is incredibly fast in Python 
            # and prevents any edge boundary indexing errors
            import bisect
            idx_start = bisect.bisect_left(arr, low)
            idx_end = bisect.bisect_right(arr, high)
            return idx_end - idx_start
            
        raise ValueError(f"Unknown operation: {op}")

    def execute_batch(self, queries: List[Dict[str, Any]]) -> Tuple[List[int], float]:
        start_time = time.perf_counter()
        answers = [self.answer_query(q) for q in queries]
        duration_ms = (time.perf_counter() - start_time) * 1000
        return answers, duration_ms

def compute_verification_hash(answers: List[int]) -> str:
    payload = ",".join(str(a) for a in answers)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()