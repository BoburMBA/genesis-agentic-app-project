#!/usr/bin/env python3
"""
GENESIS Platform — Seed Script
Run after docker-compose up to initialize agents and skills.
Usage: python scripts/seed.py [--url http://localhost:8000]
"""
import argparse
import json
import sys
import time
import urllib.request
import urllib.error


def req(url, method="GET", data=None):
    body = json.dumps(data).encode() if data else None
    headers = {"Content-Type": "application/json"}
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"HTTP {e.code}: {body[:200]}")


def wait_for_backend(base, retries=20, delay=5):
    print(f"  Waiting for backend at {base}...")
    for i in range(retries):
        try:
            health = req(f"{base}/api/v1/system/health")
            if health.get("status") == "operational":
                print(f"  ✓ Backend is healthy")
                return True
        except Exception:
            pass
        print(f"  Attempt {i+1}/{retries} — retrying in {delay}s...")
        time.sleep(delay)
    return False


def main():
    parser = argparse.ArgumentParser(description="Seed GENESIS platform")
    parser.add_argument("--url", default="http://localhost:8000", help="Backend URL")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    print("\n🧬 GENESIS AI Platform — Seed Script")
    print("=" * 45)

    # Wait for backend
    if not wait_for_backend(base):
        print("✗ Backend did not become healthy. Is docker-compose running?")
        sys.exit(1)

    # Seed agents
    print("\n[1/3] Seeding agents...")
    try:
        result = req(f"{base}/api/v1/agents/seed")
        agents = result.get("agents", [])
        print(f"  ✓ {len(agents)} agents seeded:")
        for a in agents:
            print(f"      {a['name']} ({a['type']}) — fitness {a['fitness_score']:.2f} — gen {a['generation']}")
    except Exception as e:
        print(f"  ✗ Agent seed failed: {e}")
        sys.exit(1)

    # Seed skills
    print("\n[2/3] Seeding skills...")
    try:
        result = req(f"{base}/api/v1/skills/seed")
        count = result.get("count", 0)
        skills = result.get("skills", [])
        if result.get("status") == "already_seeded":
            print(f"  ✓ Skills already seeded ({result.get('count')} in database)")
        else:
            print(f"  ✓ {count} skills seeded:")
            for s in skills:
                print(f"      {s}")
    except Exception as e:
        print(f"  ✗ Skills seed failed: {e}")

    # Run a test task
    print("\n[3/3] Running test task...")
    try:
        result = req(f"{base}/api/v1/tasks", method="POST", data={
            "task": "Say hello and briefly describe what you can do as a GENESIS AI agent.",
            "session_id": "seed-test"
        })
        print(f"  ✓ Task completed by {result.get('agent_name')} ({result.get('agent_type')})")
        print(f"  ✓ Latency: {result.get('latency_ms', 0)}ms | Tokens: {result.get('tokens_output', 0)}")
        output = result.get("output", "")[:200]
        print(f"\n  Response preview:\n  {output}{'...' if len(output) == 200 else ''}")
    except Exception as e:
        print(f"  ✗ Test task failed: {e}")

    # Print stats
    print("\n📊 Platform Stats:")
    try:
        stats = req(f"{base}/api/v1/system/stats")
        a = stats["agents"]
        t = stats["tasks"]
        print(f"  Agents:   {a['active']} active, avg fitness {a['avg_fitness']:.3f}")
        print(f"  Tasks:    {t['total']} total")
        print(f"  Skills:   {stats['skills']['active']} active")
    except Exception as e:
        print(f"  Could not fetch stats: {e}")

    print("\n✅ GENESIS is ready!")
    print(f"\n  Frontend:  http://localhost:3000")
    print(f"  Backend:   {base}")
    print(f"  API Docs:  {base}/docs")
    print(f"  Qdrant:    http://localhost:6333/dashboard")
    print()


if __name__ == "__main__":
    main()
