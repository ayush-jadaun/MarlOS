import sys
import os
import time
import asyncio
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

async def tiny_task():
    """A task that does nothing but use the event loop"""
    pass

async def stress_test(iterations=1000000):
    """Schedule massive number of tasks to stress the loop"""
    start = time.time()
    # Create 1 million tasks
    # We use a list comp to schedule them all immediately
    await asyncio.gather(*[tiny_task() for _ in range(iterations)])
    end = time.time()
    return end - start

def run_benchmark(use_winloop=False):
    # 1. Setup the Loop Policy based on flag
    if use_winloop:
        if sys.platform == 'win32':
            import winloop
            asyncio.set_event_loop_policy(winloop.EventLoopPolicy())
            print(f"🚀 Testing with WINLOOP...")
        else:
             import uvloop
             asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
             print(f"🚀 Testing with UVLOOP...")
    else:
        # Force default loop by setting policy to Default
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        print(f"🐢 Testing with STANDARD asyncio...")

    # 2. Run Test
    try:
        duration = asyncio.run(stress_test())
        print(f"⏱️  Time taken: {duration:.4f} seconds")
        print(f"📈 Throughput: {1_000_000 / duration:,.0f} tasks/sec\n")
        return duration
    except Exception as e:
        print(f"Test failed: {e}")
        return 0

if __name__ == "__main__":
    print("=== EVENT LOOP PERFORMANCE SHOWDOWN (1 Million Tasks) ===\n")
    
    # Run with Standard
    std_time = run_benchmark(use_winloop=False)
    
    # Run with Winloop/Uvloop
    opt_time = run_benchmark(use_winloop=True)

    # Calculate Improvement
    if std_time and opt_time:
        improvement = ((std_time - opt_time) / std_time) * 100
        speedup = std_time / opt_time
        print(f"🏆 WINNER: {'Winloop/Uvloop' if opt_time < std_time else 'Standard'}")
        print(f"⚡ Speedup: {speedup:.2f}x faster ({improvement:.1f}% improvement)")