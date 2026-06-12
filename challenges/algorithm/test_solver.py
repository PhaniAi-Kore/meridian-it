import unittest
from solver import AlgorithmicQueryEngine, compute_verification_hash

class TestAlgorithmicQueryEngine(unittest.TestCase):
    def setUp(self):
        self.mock_records = [
            {"user_segment": "premium", "status_code": 500, "endpoint": "/api/v1/orders", "method": "POST", "latency_ms": 1500, "request_bytes": 500},
            {"user_segment": "premium", "status_code": 500, "endpoint": "/api/v1/auth", "method": "GET", "latency_ms": 2500, "request_bytes": 1200},
            {"user_segment": "trial", "status_code": 200, "endpoint": "/api/v1/orders", "method": "POST", "latency_ms": 1000, "request_bytes": 300},
        ]
        self.engine = AlgorithmicQueryEngine()
        self.engine.preprocess(self.mock_records)

    def test_count_query(self):
        q = {"op": "count", "user_segment": "premium", "status_code": 500}
        self.assertEqual(self.engine.answer_query(q), 2)
        
        q_zero = {"op": "count", "user_segment": "trial", "status_code": 500}
        self.assertEqual(self.engine.answer_query(q_zero), 0)

    def test_exists_query(self):
        q_exists = {
            "op": "exists", "endpoint": "/api/v1/orders", "method": "POST", 
            "status_code": 500, "user_segment": "premium"
        }
        self.assertEqual(self.engine.answer_query(q_exists), 1)

        q_not_exists = {
            "op": "exists", "endpoint": "/api/v1/orders", "method": "POST", 
            "status_code": 404, "user_segment": "trial"
        }
        self.assertEqual(self.engine.answer_query(q_not_exists), 0)

    def test_range_count_query(self):
        q_range = {"op": "range_count", "field": "latency_ms", "min": 1000, "max": 2000}
        self.assertEqual(self.engine.answer_query(q_range), 2) # 1000 and 1500

    def test_hash_generation(self):
        answers = [2, 1, 0]
        expected_hash = "64c8b2ed33116df081cd29cb25668efbf9d24838634563cfd297a781b0726f1c"
        self.assertEqual(compute_verification_hash(answers), expected_hash)

if __name__ == "__main__":
    unittest.main()
