# Exercise: Drift Detection Implementation

## Task

Implement a basic drift detection system for a RAG application.

## Requirements

1. Create a Python script that monitors query distribution changes
2. Calculate PSI (Population Stability Index) for drift detection
3. Set up alerting when drift exceeds threshold

## Starter Code

```python
import numpy as np
from collections import defaultdict
from datetime import datetime, timedelta

class DriftDetector:
    def __init__(self, baseline_period_days=7, threshold=0.1):
        self.baseline_data = []
        self.current_data = []
        self.baseline_period_days = baseline_period_days
        self.threshold = threshold
        self.drift_detected = False
    
    def calculate_psi(self, expected, actual, buckets=10):
        """
        Calculate Population Stability Index
        PSI > 0.2: significant drift
        0.1 < PSI <= 0.2: moderate drift
        PSI <= 0.1: no significant drift
        """
        # Create buckets
        min_val = min(min(expected), min(actual))
        max_val = max(max(expected), max(actual))
        bucket_size = (max_val - min_val) / buckets
        
        # Calculate expected percentages
        expected_counts = np.zeros(buckets)
        for val in expected:
            bucket_idx = min(int((val - min_val) / bucket_size), buckets - 1)
            expected_counts[bucket_idx] += 1
        expected_pct = (expected_counts + 1) / (len(expected) + buckets)
        
        # Calculate actual percentages
        actual_counts = np.zeros(buckets)
        for val in actual:
            bucket_idx = min(int((val - min_val) / bucket_size), buckets - 1)
            actual_counts[bucket_idx] += 1
        actual_pct = (actual_counts + 1) / (len(actual) + buckets)
        
        # Calculate PSI
        psi = np.sum((actual_pct - expected_pct) * 
                     np.log(actual_pct / expected_pct))
        
        return psi
    
    def add_sample(self, query_length):
        """Add a query length sample for monitoring"""
        self.current_data.append(query_length)
    
    def check_drift(self):
        """Check if drift has occurred"""
        if len(self.baseline_data) < 100 or len(self.current_data) < 100:
            return False, "Insufficient data"
        
        psi = self.calculate_psi(self.baseline_data, self.current_data)
        
        if psi > self.threshold:
            self.drift_detected = True
            return True, f"Drift detected! PSI: {psi:.4f}"
        
        return False, f"No drift. PSI: {psi:.4f}"
    
    def set_baseline(self):
        """Set current data as baseline"""
        self.baseline_data = self.current_data.copy()
        self.current_data = []
        self.drift_detected = False


# Test the drift detector
if __name__ == "__main__":
    detector = DriftDetector(threshold=0.2)
    
    # Simulate baseline data (query lengths)
    baseline_lengths = np.random.normal(50, 10, 500)
    for length in baseline_lengths:
        detector.add_sample(length)
    
    detector.set_baseline()
    
    # Simulate new data with drift
    drifted_lengths = np.random.normal(70, 15, 500)
    for length in drifted_lengths:
        detector.add_sample(length)
    
    is_drift, message = detector.check_drift()
    print(message)
```

## Deliverable

Create a complete drift detection module with:
- PSI calculation
- Real-time monitoring
- Alert integration
- Visualization of drift metrics

## Solution

See solution.py for a complete implementation.
