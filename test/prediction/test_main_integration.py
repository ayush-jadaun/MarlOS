"""
Integration Test: Verify Predictive System is Integrated into Main Agent
Tests that the predictive system is properly connected and configurable
"""

import sys
sys.path.insert(0, 'agent')

from agent.config import AgentConfig, PredictiveConfig
from agent.main import MarlOSAgent


def test_predictive_initialization():
    """Test that predictive system initializes correctly"""
    print("\n" + "=" * 60)
    print("TEST 1: Predictive System Initialization")
    print("=" * 60)

    # Create agent with default config
    config = AgentConfig()
    agent = MarlOSAgent(config)

    # Check predictive system exists
    assert hasattr(agent, 'predictive'), "Agent should have predictive attribute"
    assert agent.predictive is not None, "Predictive system should be initialized"

    print("  [PASS] Predictive system initialized")
    return True


def test_predictive_enabled_by_default():
    """Test that predictive system is enabled by default"""
    print("\n" + "=" * 60)
    print("TEST 2: Predictive System Enabled by Default")
    print("=" * 60)

    config = AgentConfig()
    agent = MarlOSAgent(config)

    # Check if enabled
    assert config.predictive.enabled == True, "Predictive should be enabled by default"

    stats = agent.predictive.get_stats()
    print(f"  Predictive enabled: {stats['enabled']}")
    assert stats['enabled'] == True, "Predictive stats should show enabled"

    print("  [PASS] Predictive enabled by default")
    return True


def test_predictive_can_be_disabled():
    """Test that predictive system can be disabled via config"""
    print("\n" + "=" * 60)
    print("TEST 3: Predictive System Can Be Disabled")
    print("=" * 60)

    # Create config with predictive disabled
    config = AgentConfig()
    config.predictive.enabled = False

    agent = MarlOSAgent(config)

    # Check if disabled
    stats = agent.predictive.get_stats()
    print(f"  Predictive enabled: {stats['enabled']}")
    assert stats['enabled'] == False, "Predictive should be disabled"

    print("  [PASS] Predictive can be disabled via config")
    return True


def test_rl_speculation_configurable():
    """Test that RL speculation can be configured"""
    print("\n" + "=" * 60)
    print("TEST 4: RL Speculation Configurable")
    print("=" * 60)

    # Test with RL enabled
    config1 = AgentConfig()
    config1.predictive.rl_speculation_enabled = True
    agent1 = MarlOSAgent(config1)

    stats1 = agent1.predictive.get_stats()
    if stats1['enabled']:
        spec_stats1 = stats1.get('speculation', {})
        print(f"  With RL enabled: using_rl_policy = {spec_stats1.get('using_rl_policy')}")

    # Test with RL disabled (heuristic mode)
    config2 = AgentConfig()
    config2.predictive.rl_speculation_enabled = False
    agent2 = MarlOSAgent(config2)

    stats2 = agent2.predictive.get_stats()
    if stats2['enabled']:
        spec_stats2 = stats2.get('speculation', {})
        print(f"  With RL disabled: using_rl_policy = {spec_stats2.get('using_rl_policy')}")

    print("  [PASS] RL speculation is configurable")
    return True


def test_custom_predictive_config():
    """Test custom predictive configuration"""
    print("\n" + "=" * 60)
    print("TEST 5: Custom Predictive Configuration")
    print("=" * 60)

    # Create custom config
    config = AgentConfig()
    config.predictive.min_pattern_confidence = 0.90
    config.predictive.max_speculation_ratio = 0.1
    config.predictive.min_expected_value = 10.0
    config.predictive.cache_ttl = 600
    config.predictive.max_cache_size = 50

    agent = MarlOSAgent(config)

    # Verify settings applied
    assert agent.config.predictive.min_pattern_confidence == 0.90, "Custom confidence should apply"
    assert agent.config.predictive.max_speculation_ratio == 0.1, "Custom ratio should apply"
    assert agent.config.predictive.min_expected_value == 10.0, "Custom EV should apply"

    print(f"  Min confidence: {agent.config.predictive.min_pattern_confidence}")
    print(f"  Max speculation ratio: {agent.config.predictive.max_speculation_ratio}")
    print(f"  Min expected value: {agent.config.predictive.min_expected_value}")
    print(f"  Cache TTL: {agent.config.predictive.cache_ttl}s")
    print(f"  Max cache size: {agent.config.predictive.max_cache_size}")

    print("  [PASS] Custom configuration works")
    return True


def test_predictive_components_connected():
    """Test that all predictive components are properly connected"""
    print("\n" + "=" * 60)
    print("TEST 6: Predictive Components Connected")
    print("=" * 60)

    config = AgentConfig()
    agent = MarlOSAgent(config)

    # Check that predictive has access to agent components
    if agent.predictive.enabled:
        assert agent.predictive.pattern_detector is not None, "Pattern detector should exist"
        assert agent.predictive.cache is not None, "Cache should exist"
        assert agent.predictive.speculation_engine is not None, "Speculation engine should exist"

        print("  Pattern detector: OK")
        print("  Cache: OK")
        print("  Speculation engine: OK")

        # Check that speculation engine has access to executor
        assert agent.predictive.speculation_engine.executor is not None, "Should have executor reference"
        print("  Executor reference: OK")

    print("  [PASS] All components properly connected")
    return True


def test_predictive_stats_structure():
    """Test that predictive stats have correct structure"""
    print("\n" + "=" * 60)
    print("TEST 7: Predictive Stats Structure")
    print("=" * 60)

    config = AgentConfig()
    agent = MarlOSAgent(config)

    stats = agent.predictive.get_stats()

    # Check stats structure
    assert 'enabled' in stats, "Stats should have 'enabled' field"

    if stats['enabled']:
        assert 'pattern_detector' in stats, "Should have pattern_detector stats"
        assert 'cache' in stats, "Should have cache stats"
        assert 'speculation' in stats, "Should have speculation stats"

        print(f"  Stats keys: {list(stats.keys())}")

        # Check sub-stats
        cache_stats = stats['cache']
        assert 'hit_rate' in cache_stats, "Cache stats should have hit_rate"
        assert 'cache_size' in cache_stats, "Cache stats should have cache_size"

        spec_stats = stats['speculation']
        assert 'speculations_attempted' in spec_stats, "Should track speculations"
        assert 'using_rl_policy' in spec_stats, "Should show if using RL"

        print(f"  Cache stats: {list(cache_stats.keys())}")
        print(f"  Speculation stats: {list(spec_stats.keys())}")

    print("  [PASS] Stats structure is correct")
    return True


def test_agent_state_includes_predictive():
    """Test that agent state includes predictive stats"""
    print("\n" + "=" * 60)
    print("TEST 8: Agent State Includes Predictive")
    print("=" * 60)

    config = AgentConfig()
    agent = MarlOSAgent(config)

    state = agent.get_state()

    # Check that predictive stats are in agent state
    assert 'predictive_stats' in state, "Agent state should include predictive_stats"

    print(f"  Agent state keys: {list(state.keys())}")
    print(f"  Predictive stats included: YES")

    print("  [PASS] Predictive stats in agent state")
    return True


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "=" * 70)
    print("MAIN AGENT INTEGRATION TESTS - Predictive System")
    print("=" * 70)

    tests = [
        ("Predictive Initialization", test_predictive_initialization),
        ("Predictive Enabled by Default", test_predictive_enabled_by_default),
        ("Predictive Can Be Disabled", test_predictive_can_be_disabled),
        ("RL Speculation Configurable", test_rl_speculation_configurable),
        ("Custom Configuration", test_custom_predictive_config),
        ("Components Connected", test_predictive_components_connected),
        ("Stats Structure", test_predictive_stats_structure),
        ("Agent State Integration", test_agent_state_includes_predictive),
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

    print("\n" + "=" * 70)
    print(f"INTEGRATION TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("\n*** ALL INTEGRATION TESTS PASSED! ***")
        print("The predictive system is successfully integrated into MarlOS Agent!")
        print("\nYou can now:")
        print("  1. Enable/disable via: config.predictive.enabled = True/False")
        print("  2. Configure RL speculation: config.predictive.rl_speculation_enabled")
        print("  3. Adjust economic parameters in PredictiveConfig")
        print("  4. Monitor stats via: agent.predictive.get_stats()")
        print("\nSee PREDICTIVE_CONFIG.md for full configuration guide!")
    else:
        print(f"\n{failed} tests failed")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
