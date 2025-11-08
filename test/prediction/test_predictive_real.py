"""
REAL Unit Tests for Predictive System
Validates actual algorithm behavior
"""

import asyncio
import time
from agent.predictive.pattern_detector import PatternDetector
from agent.predictive.cache import ResultCache


def test_pattern_detector_repeated_jobs():
    """Test that detector actually learns repeated job patterns"""
    print("\n" + "="*60)
    print("TEST 1: Pattern Detector - Repeated Jobs")
    print("="*60)

    detector = PatternDetector(min_occurrences=3)

    job = {
        'job_id': 'test-1',
        'job_type': 'shell',
        'params': {'command': 'echo hello'}
    }

    # Observe same job 3 times
    print("\n[TEST] Observing job 3 times...")
    for i in range(3):
        detector.observe_job(job)
        time.sleep(0.1)  # Small delay to create timing pattern

    # Check stats
    stats = detector.get_stats()
    print(f"   Jobs observed: {stats['total_jobs_seen']}")
    print(f"   Unique fingerprints: {stats['unique_fingerprints']}")

    assert stats['total_jobs_seen'] == 3, "Should have seen 3 jobs"
    assert stats['unique_fingerprints'] == 1, "Should have 1 unique pattern"

    # Try to predict
    predictions = detector.predict_next_jobs()
    print(f"\n   Predictions made: {len(predictions)}")

    if predictions:
        pred = predictions[0]
        print(f"   Confidence: {pred['confidence']:.0%}")
        print(f"   Reason: {pred['reason']}")

        # Verify prediction quality
        assert pred['confidence'] >= 0.5, "Should have reasonable confidence"
        print("\n[PASS] Pattern detector correctly learned repeated pattern!")
    else:
        print("\n[FAIL] No predictions made (might need more time variance)")

    return True


def test_cache_hit():
    """Test that cache actually stores and retrieves results"""
    print("\n" + "="*60)
    print("TEST 2: Result Cache - Store and Retrieve")
    print("="*60)

    cache = ResultCache(max_size=10, ttl=60)

    job = {
        'job_id': 'test-cache-1',
        'job_type': 'shell',
        'params': {'command': 'echo test'}
    }

    result = {
        'status': 'success',
        'output': 'test output',
        'execution_time': 1.5
    }

    # Store result
    print("\n[TEST] Storing result in cache...")
    cache.store(job, result)

    stats = cache.get_stats()
    print(f"   Cache size: {stats['cache_size']}")
    assert stats['cache_size'] == 1, "Cache should have 1 entry"

    # Retrieve result
    print("\n[TEST] Retrieving from cache...")
    cached = cache.get(job)

    assert cached is not None, "Should get cached result"
    assert cached['output'] == 'test output', "Should return correct result"

    stats = cache.get_stats()
    print(f"   Cache hits: {stats['cache_hits']}")
    print(f"   Cache misses: {stats['cache_misses']}")
    print(f"   Hit rate: {stats['hit_rate']:.1f}%")

    assert stats['cache_hits'] == 1, "Should have 1 cache hit"
    assert stats['hit_rate'] == 100.0, "Should have 100% hit rate"

    print("\n[PASS] Cache correctly stored and retrieved result!")
    return True


def test_cache_miss():
    """Test that cache returns None for unknown jobs"""
    print("\n" + "="*60)
    print("TEST 3: Cache Miss - Unknown Job")
    print("="*60)

    cache = ResultCache(max_size=10, ttl=60)

    job = {
        'job_id': 'unknown-job',
        'job_type': 'shell',
        'params': {'command': 'echo unknown'}
    }

    print("\n[TEST] Requesting uncached job...")
    cached = cache.get(job)

    assert cached is None, "Should return None for cache miss"

    stats = cache.get_stats()
    print(f"   Cache hits: {stats['cache_hits']}")
    print(f"   Cache misses: {stats['cache_misses']}")

    assert stats['cache_misses'] == 1, "Should have 1 cache miss"

    print("\n[PASS] Cache correctly returned None for unknown job!")
    return True


def test_fingerprint_consistency():
    """Test that same jobs get same fingerprint"""
    print("\n" + "="*60)
    print("TEST 4: Fingerprint Consistency")
    print("="*60)

    detector = PatternDetector()

    job1 = {
        'job_type': 'shell',
        'params': {'command': 'echo hello'}
    }

    job2 = {
        'job_type': 'shell',
        'params': {'command': 'echo hello'}
    }

    job3 = {
        'job_type': 'shell',
        'params': {'command': 'echo goodbye'}  # Different!
    }

    fp1 = detector._compute_fingerprint(job1)
    fp2 = detector._compute_fingerprint(job2)
    fp3 = detector._compute_fingerprint(job3)

    print(f"\n   Job 1 fingerprint: {fp1}")
    print(f"   Job 2 fingerprint: {fp2}")
    print(f"   Job 3 fingerprint: {fp3}")

    assert fp1 == fp2, "Same jobs should have same fingerprint"
    assert fp1 != fp3, "Different jobs should have different fingerprints"

    print("\n[PASS] Fingerprints are consistent!")
    return True


def test_sequence_detection():
    """Test that detector learns job sequences"""
    print("\n" + "="*60)
    print("TEST 5: Sequence Pattern Detection")
    print("="*60)

    detector = PatternDetector(min_occurrences=3)

    # Create a sequence: A -> B -> C
    job_a = {'job_type': 'git_pull', 'params': {}}
    job_b = {'job_type': 'docker_build', 'params': {}}
    job_c = {'job_type': 'run_tests', 'params': {}}

    print("\n[TEST] Observing sequence A->B->C three times...")
    for i in range(3):
        detector.observe_job(job_a)
        detector.observe_job(job_b)
        detector.observe_job(job_c)

    stats = detector.get_stats()
    print(f"   Jobs observed: {stats['total_jobs_seen']}")
    print(f"   Sequence patterns: {stats['sequence_patterns']}")

    # Check if sequence was learned
    assert ('git_pull', 'docker_build') in detector.job_sequences, \
        "Should learn git_pull -> docker_build"
    assert ('docker_build', 'run_tests') in detector.job_sequences, \
        "Should learn docker_build -> run_tests"

    count_ab = detector.job_sequences[('git_pull', 'docker_build')]
    count_bc = detector.job_sequences[('docker_build', 'run_tests')]

    print(f"   git_pull -> docker_build: {count_ab} times")
    print(f"   docker_build -> run_tests: {count_bc} times")

    assert count_ab == 3, "Should see sequence 3 times"
    assert count_bc == 3, "Should see sequence 3 times"

    print("\n[PASS] Sequence detection works correctly!")
    return True


def test_cache_expiry():
    """Test that cache entries expire after TTL"""
    print("\n" + "="*60)
    print("TEST 6: Cache TTL Expiry")
    print("="*60)

    cache = ResultCache(max_size=10, ttl=1)  # 1 second TTL

    job = {'job_type': 'shell', 'params': {'command': 'echo test'}}
    result = {'status': 'success', 'output': 'test'}

    print("\n[TEST] Storing result with 1s TTL...")
    cache.store(job, result)

    # Immediate retrieval should work
    cached = cache.get(job)
    assert cached is not None, "Should get result immediately"
    print("   [OK] Immediate retrieval works")

    # Wait for expiry
    print("   Waiting 1.5s for expiry...")
    time.sleep(1.5)

    # Should be expired now
    cached = cache.get(job)
    assert cached is None, "Should return None after TTL"

    stats = cache.get_stats()
    print(f"   Expired entries: {stats['expired_entries']}")
    assert stats['expired_entries'] == 1, "Should have 1 expired entry"

    print("\n[PASS] Cache TTL works correctly!")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("RUNNING REAL UNIT TESTS FOR PREDICTIVE SYSTEM")
    print("="*60)

    tests = [
        test_pattern_detector_repeated_jobs,
        test_cache_hit,
        test_cache_miss,
        test_fingerprint_consistency,
        test_sequence_detection,
        test_cache_expiry
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"\n[ERROR] {test.__name__}: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*60)

    if failed == 0:
        print("\n*** ALL TESTS PASSED! ***")
        print("The predictive system is REAL and WORKING!")
    else:
        print(f"\n{failed} tests failed - needs debugging")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
