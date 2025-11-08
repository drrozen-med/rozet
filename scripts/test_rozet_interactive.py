#!/usr/bin/env python3
"""
Interactive testing of Rozet REPL - simulating human usage
"""
from __future__ import annotations

import os
import pexpect
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def test_repl():
    """Run interactive REPL tests"""

    print("\n" + "="*60)
    print("ROZET INTERACTIVE TESTING - Human Simulation")
    print("="*60 + "\n")

    os.chdir(ROOT)

    # Start REPL
    print("▶ Starting rozet --repl...")
    start_time = time.time()
    child = pexpect.spawn(
        "./run.sh --repl",
        cwd=str(ROOT),
        timeout=60,
        encoding="utf-8",
    )
    child.logfile = sys.stdout

    try:
        # Wait for prompt (looking for "You:" - account for ANSI colors)
        print("\n[TEST 1] Waiting for startup...")
        child.expect(r'You.*:', timeout=60)
        elapsed = time.time() - start_time
        print(f"\n✅ REPL started in {elapsed:.1f}s")

        # Test 2: Send greeting
        print("\n[TEST 2] Sending: hello")
        start_time = time.time()
        child.sendline('hello')
        child.expect(r'You.*:', timeout=60)
        elapsed = time.time() - start_time
        print(f"\n✅ Greeting response in {elapsed:.1f}s")

        # Test 3: Help command
        print("\n[TEST 3] Sending: help")
        child.sendline('help')
        child.expect('You:', timeout=30)
        print("\n✅ Help command completed")

        # Test 4: Empty input
        print("\n[TEST 4] Sending: (empty)")
        child.sendline('')
        child.expect('You:', timeout=10)
        print("\n✅ Empty input handled")

        # Test 5: Simple task
        print("\n[TEST 5] Sending: create a file test.txt with hello world")
        start_time = time.time()
        child.sendline('create a file test.txt with hello world')
        child.expect('You:', timeout=120)
        elapsed = time.time() - start_time
        print(f"\n✅ Simple task completed in {elapsed:.1f}s")

        # Test 6: Exit
        print("\n[TEST 6] Sending: exit")
        child.sendline('exit')
        child.expect(pexpect.EOF, timeout=10)
        print("\n✅ Clean exit")

        print("\n" + "="*60)
        print("ALL TESTS PASSED ✅")
        print("="*60 + "\n")

        return True

    except pexpect.TIMEOUT as e:
        print(f"\n❌ TIMEOUT: {e}")
        print(f"Last output: {child.before}")
        return False
    except pexpect.EOF as e:
        print(f"\n❌ Unexpected EOF: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    finally:
        if child.isalive():
            child.close()

if __name__ == '__main__':
    success = test_repl()
    sys.exit(0 if success else 1)
