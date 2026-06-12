import time
from typing import List, Dict, Any, Union
from pydantic import BaseModel

class QueryItem(BaseModel):
    type: str  # 'count', 'exists', 'range_count'
    value: Union[int, List[int]]

class BatchQueryPayload(BaseModel):
    dataset: List[int]
    queries: List[QueryItem]

def process_fast_queries(payload: BatchQueryPayload) -> Dict[str, Any]:
    """
    Executes algorithmic verification over Jumbo data collections.
    Preprocessing: O(N)
    Query Evaluation: O(1) per execution item -> O(K) total
    """
    start_time = time.perf_counter()
    
    freq_map = {}
    max_val = 0
    
    for val in payload.dataset:
        freq_map[val] = freq_map.get(val, 0) + 1
        if val > max_val:
            max_val = val
            
    prefix_sums = [0] * (max_val + 2)
    for i in range(1, max_val + 2):
        prefix_sums[i] = prefix_sums[i - 1] + freq_map.get(i - 1, 0)

    results = []
    for q in payload.queries:
        if q.type == "count":
            results.append(freq_map.get(q.value, 0))
            
        elif q.type == "exists":
            results.append(q.value in freq_map)
            
        elif q.type == "range_count":
            low, high = q.value[0], q.value[1]
            if low > max_val:
                results.append(0)
                continue
            high = min(high, max_val)
            results.append(prefix_sums[high + 1] - prefix_sums[low])
        else:
            results.append(None)

    execution_ms = (time.perf_counter() - start_time) * 1000
    return {
        "execution_time_ms": round(execution_ms, 2),
        "processed_queries": len(results),
        "results": results
    }
