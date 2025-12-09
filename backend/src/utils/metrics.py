"""
Performance metrics and monitoring utilities
"""

import time
from typing import Dict, List
from collections import defaultdict
import statistics

class MetricsCollector:
    """Collect and aggregate performance metrics"""
    
    def __init__(self):
        self.latencies: Dict[str, List[float]] = defaultdict(list)
        self.counters: Dict[str, int] = defaultdict(int)
        self.start_time = time.time()
    
    def record_latency(self, operation: str, duration_ms: float):
        """Record operation latency"""
        self.latencies[operation].append(duration_ms)
    
    def increment_counter(self, counter: str, value: int = 1):
        """Increment a counter"""
        self.counters[counter] += value


    def get_stats(self, operation: str) -> Dict:
        """Get statistics for an operation"""
        if operation not in self.latencies or not self.latencies[operation]:
            return {}
        
        latencies = self.latencies[operation]
        return {
            'count': len(latencies),
            'mean': statistics.mean(latencies),
            'median': statistics.median(latencies),
            'p95': self._percentile(latencies, 95),
            'p99': self._percentile(latencies, 99),
            'min': min(latencies),
            'max': max(latencies)
        }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def get_all_stats(self) -> Dict:
        """Get all statistics"""
        return {
            'operations': {op: self.get_stats(op) for op in self.latencies},
            'counters': dict(self.counters),
            'uptime_seconds': time.time() - self.start_time
        }
    def reset(self):
        """Reset all metrics"""
        self.latencies.clear()
        self.counters.clear()
        self.start_time = time.time()

class Timer: 
     """Context manager for timing operations"""
     def __init__(self, operation: str, collector: MetricsCollector = None):
        self.operation = operation
        self.collector = collector
        self.start_time = None
        self.duration_ms = None
    
     def __enter__(self):
         self.start_time = time.time()
         return self
     
     def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration_ms = (time.time() - self.start_time) * 1000
        if self.collector:
            self.collector.record_latency(self.operation, self.duration_ms)

    