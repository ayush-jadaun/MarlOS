import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import time
import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
from agent.crypto.signing import SigningKey, sign_message, verify_message
from agent.crypto.encryption import AsymmetricEncryption, encrypt_job_payload, decrypt_job_payload
from agent.p2p.security import ReplayProtection, generate_nonce
from agent.p2p.node import RateLimiter

# Setup output directory for charts
OUTPUT_DIR = "benchmark_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set visual style
sns.set_theme(style="whitegrid")

class BenchmarkSuite:
    def __init__(self):
        self.results = {}
        print(f"🚀 Starting Benchmark Suite")
        print(f"📁 Charts will be saved to: {os.path.abspath(OUTPUT_DIR)}/\n")

    def run_all(self):
        self.benchmark_crypto_overhead()
        self.benchmark_rate_limiter()
        self.benchmark_pipeline_latency()
        print("\n✅ All benchmarks completed successfully!")

    def benchmark_crypto_overhead(self, iterations=1000):
        """Case 1: The Security Tax - Measuring throughput under different security levels"""
        print(f"📊 Running Case 1: Crypto Overhead Analysis ({iterations} iterations)...")
        
        payload = {"type": "job_bid", "job_id": "job-123", "bid": 50.0, "node_id": "node-A"}
        key = SigningKey.generate()
        enc_sender = AsymmetricEncryption()
        enc_recipient = AsymmetricEncryption()
        recipient_pub = enc_recipient.public_key_hex()

        times = {'Config': [], 'Messages/Sec': []}

        # --- Config A: Baseline (Raw JSON) ---
        start = time.time()
        for _ in range(iterations):
            _ = json.dumps(payload)
        duration = time.time() - start
        times['Config'].append('Baseline (JSON only)')
        times['Messages/Sec'].append(iterations / duration)

        # --- Config B: Integrity (Signed) ---
        start = time.time()
        for _ in range(iterations):
            # Simulate full send/receive cycle
            msg = payload.copy()
            signed = sign_message(key, msg)
            verify_message(signed)
        duration = time.time() - start
        times['Config'].append('Integrity (Signed)')
        times['Messages/Sec'].append(iterations / duration)

        # --- Config C: Privacy (Signed + Encrypted) ---
        start = time.time()
        for _ in range(iterations):
            # Full cycle: Encrypt payload -> Sign -> Verify -> Decrypt payload
            msg = payload.copy()
            # 1. Encrypt a field
            secret = {"secret_data": "some api key"}
            msg['encrypted_payload'] = encrypt_job_payload(secret, recipient_pub, enc_sender)
            # 2. Sign
            signed = sign_message(key, msg)
            # 3. Verify
            verify_message(signed)
            # 4. Decrypt
            _ = decrypt_job_payload(msg['encrypted_payload'], enc_sender.public_key_hex(), enc_recipient)

        duration = time.time() - start
        times['Config'].append('Privacy (Full Encryption)')
        times['Messages/Sec'].append(iterations / duration)

        # Plotting
        df = pd.DataFrame(times)
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(data=df, x='Config', y='Messages/Sec', palette='viridis')
        ax.set_title('The "Security Tax": Max Theoretical Throughput per CPU Core', fontsize=14)
        ax.bar_label(ax.containers[0], fmt='%.0f')
        plt.ylabel("Messages Processed per Second")
        plt.savefig(f"{OUTPUT_DIR}/case1_crypto_overhead.png")
        plt.close()

    def benchmark_rate_limiter(self):
        """Case 2: DDoS Resistance - Simulating a flood attack"""
        print("📊 Running Case 2: Rate Limiter Stress Test (DDoS Simulation)...")
        
        # Setup: Allow 10 burst, refill 50 per second (high throughput test)
        limiter = RateLimiter(max_tokens=100, refill_rate=50.0)
        
        history = {'Time': [], 'Status': []}
        start_time = time.time()
        
        # 1. Normal traffic (1 sec)
        for _ in range(50):
            time.sleep(0.02) # 50 msg/sec
            res = limiter.consume()
            history['Time'].append(time.time() - start_time)
            history['Status'].append('Accepted' if res else 'Dropped')

        # 2. BURST ATTACK! (1000 messages instantly)
        for _ in range(1000):
            res = limiter.consume()
            history['Time'].append(time.time() - start_time)
            history['Status'].append('Accepted' if res else 'Dropped')

        # 3. Recovery period (1 sec)
        for _ in range(50):
            time.sleep(0.02)
            res = limiter.consume()
            history['Time'].append(time.time() - start_time)
            history['Status'].append('Accepted' if res else 'Dropped')

        # Plotting
        df = pd.DataFrame(history)
        # Bin data by 0.1s intervals for cleaner plotting
        df['TimeBin'] = df['Time'].round(1)
        summary = df.groupby(['TimeBin', 'Status']).size().reset_index(name='Count')

        plt.figure(figsize=(12, 6))
        sns.lineplot(data=summary, x='TimeBin', y='Count', hue='Status', 
                     palette={'Accepted': 'green', 'Dropped': 'red'}, marker="o")
        plt.title('DDoS Simulation: Rate Limiter Response to 1000-msg Burst', fontsize=14)
        plt.xlabel("Time (seconds)")
        plt.ylabel("Messages per 0.1s interval")
        plt.axvspan(1.0, 1.1, color='red', alpha=0.1, label='Attack Burst')
        plt.legend()
        plt.savefig(f"{OUTPUT_DIR}/case2_ddos_resistance.png")
        plt.close()

    def benchmark_pipeline_latency(self, samples=5000):
        """Case 3: Pipeline Latency - p99 Analysis"""
        print(f"📊 Running Case 3: Full Security Pipeline Latency ({samples} samples)...")
        
        replay = ReplayProtection()
        key = SigningKey.generate()
        base_msg = {"type": "heartbeat", "node_id": "node-A", "data": "x" * 1000} # 1KB payload
        
        latencies_ms = []

        for i in tqdm(range(samples)):
            # 1. Create & Sign (Sender side - not counted in receiver latency)
            msg = base_msg.copy()
            msg['timestamp'] = time.time()
            msg['nonce'] = generate_nonce()
            msg['message_id'] = f"msg-{i}"
            signed = sign_message(key, msg)
            
            # Start timer (Receiver side starts here)
            start = time.perf_counter()
            
            # --- The Pipeline ---
            # 1. Verify Signature
            if not verify_message(signed): raise Exception("Sig failed")
            # 2. Replay Check
            valid, _ = replay.validate_message(signed)
            if not valid: raise Exception("Replay failed")
            replay.mark_message_seen(signed)
            # --------------------
            
            end = time.perf_counter()
            latencies_ms.append((end - start) * 1000)

        # Calculate percentiles
        p50 = np.percentile(latencies_ms, 50)
        p95 = np.percentile(latencies_ms, 95)
        p99 = np.percentile(latencies_ms, 99)

        print(f"   Latency p50: {p50:.3f}ms")
        print(f"   Latency p99: {p99:.3f}ms")

        # Plotting
        plt.figure(figsize=(10, 6))
        sns.histplot(latencies_ms, kde=True, color="blue", bins=50)
        plt.axvline(p95, color='orange', linestyle='--', label=f'p95: {p95:.2f}ms')
        plt.axvline(p99, color='red', linestyle='--', label=f'p99: {p99:.2f}ms')
        plt.title('Security Pipeline Processing Latency Distribution', fontsize=14)
        plt.xlabel("Processing Time (ms)")
        plt.legend()
        plt.savefig(f"{OUTPUT_DIR}/case3_pipeline_latency.png")
        plt.close()

if __name__ == "__main__":
    suite = BenchmarkSuite()
    suite.run_all()