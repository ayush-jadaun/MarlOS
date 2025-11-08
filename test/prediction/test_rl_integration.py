"""
Integration Test: RL Speculation in Predictive System
Tests the full system with RL policy making speculation decisions
"""

import sys
sys.path.insert(0, 'agent')

from agent.predictive.pattern_detector import PatternDetector
from agent.predictive.cache import ResultCache
from agent.predictive.rl_speculation import RLSpeculationPolicy
from agent.config import PredictiveConfig


def test_rl_policy_integration():
    """Test that RL policy integrates correctly"""
    print("\n" + "=" * 60)
    print("INTEGRATION TEST: RL Policy in Predictive System")
    print("=" * 60)

    # Create config
    config = PredictiveConfig()
    config.rl_speculation_enabled = True
    config.rl_model_path = "rl_trainer/models/speculation_policy.zip"

    print(f"\n[TEST] Config:")
    print(f"  RL enabled: {config.rl_speculation_enabled}")
    print(f"  Model path: {config.rl_model_path}")

    # Create RL policy
    policy = RLSpeculationPolicy(
        model_path=config.rl_model_path,
        enabled=config.rl_speculation_enabled
    )

    print(f"\n[TEST] RL Policy created:")
    print(f"  Model loaded: {policy.model is not None}")

    # Test decision making
    prediction = {
        'confidence': 0.85,
        'expected_in': 30,
        'reason': 'repeated_job'
    }

    context = {
        'cpu_idle_pct': 0.7,
        'cache_utilization': 0.2,
        'recent_hit_rate': 0.8,
        'balance': 150,
        'active_jobs': 1
    }

    print(f"\n[TEST] Making speculation decision...")
    print(f"  Prediction confidence: {prediction['confidence']:.0%}")
    print(f"  CPU idle: {context['cpu_idle_pct']:.0%}")

    should_speculate, confidence, state = policy.decide(prediction, context)

    print(f"\n[RESULT] Decision:")
    print(f"  Should speculate: {should_speculate}")
    print(f"  Decision confidence: {confidence:.2f}")
    print(f"  State vector: {state}")

    # Get stats
    stats = policy.get_stats()
    print(f"\n[STATS]:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Verify it works
    assert isinstance(should_speculate, bool), "Should return bool"
    assert state.shape == (7,), "State should be 7D"
    assert stats['decisions_made'] == 1, "Should have 1 decision"

    print("\n[PASS] RL policy integration works!")
    return True


def test_with_and_without_rl():
    """Compare system behavior with/without RL"""
    print("\n" + "=" * 60)
    print("COMPARISON: With RL vs Without RL")
    print("=" * 60)

    # Test scenario
    prediction = {
        'confidence': 0.70,  # Medium confidence
        'expected_in': 45,
        'reason': 'sequence'
    }

    context = {
        'cpu_idle_pct': 0.9,  # Lots of idle CPU
        'cache_utilization': 0.1,  # Cache not full
        'recent_hit_rate': 0.85,  # Good hit rate
        'balance': 200,  # Good balance
        'active_jobs': 0  # Not busy
    }

    # With RL
    print("\n[WITH RL]")
    policy_rl = RLSpeculationPolicy(
        model_path="rl_trainer/models/speculation_policy.zip",
        enabled=True
    )

    should_spec_rl, conf_rl, state_rl = policy_rl.decide(prediction, context)
    print(f"  Decision: {'SPECULATE' if should_spec_rl else 'WAIT'}")
    print(f"  Confidence: {conf_rl:.2f}")
    print(f"  Model loaded: {policy_rl.model is not None}")

    # Without RL (heuristic)
    print("\n[WITHOUT RL (Heuristic)]")
    policy_heuristic = RLSpeculationPolicy(
        model_path="nonexistent.zip",
        enabled=False
    )

    should_spec_h, conf_h, state_h = policy_heuristic.decide(prediction, context)
    print(f"  Decision: {'SPECULATE' if should_spec_h else 'WAIT'}")
    print(f"  Confidence: {conf_h:.2f}")

    # Calculate expected value (heuristic logic)
    expected_value = (0.70 * 20) - (0.30 * 5)
    print(f"  Expected value: {expected_value:.1f} AC")
    print(f"  Would speculate if EV > 3.0: {expected_value >= 3.0}")

    print("\n[COMPARISON]")
    print(f"  RL uses trained model to make decision")
    print(f"  Heuristic uses simple expected value threshold")
    print(f"  Both can make good decisions, RL is more adaptive")

    print("\n[PASS] Comparison complete!")
    return True


def test_full_system_stats():
    """Test that all stats are tracked correctly"""
    print("\n" + "=" * 60)
    print("STATS TRACKING TEST")
    print("=" * 60)

    policy = RLSpeculationPolicy(
        model_path="rl_trainer/models/speculation_policy.zip",
        enabled=True
    )

    # Make several decisions
    scenarios = [
        {'confidence': 0.9, 'cpu_idle_pct': 0.8, 'balance': 200},
        {'confidence': 0.5, 'cpu_idle_pct': 0.3, 'balance': 50},
        {'confidence': 0.7, 'cpu_idle_pct': 0.6, 'balance': 150},
    ]

    print(f"\n[TEST] Making {len(scenarios)} decisions...")

    for i, context_partial in enumerate(scenarios):
        context = {
            **context_partial,
            'cache_utilization': 0.2,
            'recent_hit_rate': 0.7,
            'active_jobs': 1
        }

        prediction = {'confidence': context_partial['confidence'], 'expected_in': 30}

        should_spec, conf, state = policy.decide(prediction, context)
        print(f"  Decision {i+1}: {'SPECULATE' if should_spec else 'WAIT'} "
              f"(conf={prediction['confidence']:.0%})")

    # Check stats
    stats = policy.get_stats()

    print(f"\n[STATS]")
    print(f"  Decisions made: {stats['decisions_made']}")
    print(f"  Speculations chosen: {stats['speculations_chosen']}")
    print(f"  Speculation rate: {stats['speculation_rate']:.1f}%")
    print(f"  Model loaded: {stats['model_loaded']}")

    assert stats['decisions_made'] == 3, "Should have 3 decisions"
    assert stats['decisions_made'] > 0, "Should track decisions"

    print("\n[PASS] Stats tracking works!")
    return True


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print("RUNNING RL INTEGRATION TESTS")
    print("=" * 60)

    tests = [
        ("RL Policy Integration", test_rl_policy_integration),
        ("With/Without RL Comparison", test_with_and_without_rl),
        ("Stats Tracking", test_full_system_stats),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"\n[FAIL] {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"\n[ERROR] {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"INTEGRATION TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n*** ALL INTEGRATION TESTS PASSED! ***")
        print("RL policy is successfully integrated into the predictive system!")
    else:
        print(f"\n{failed} tests failed")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
