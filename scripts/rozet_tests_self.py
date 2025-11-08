#!/usr/bin/env python3
"""
Use Rozet to test and improve itself
"""
from __future__ import annotations

import os
import pexpect
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def send_and_wait(child, command, timeout=120, auto_confirm=True):
    """Send command and wait for response, handling interactive prompts"""
    print(f"\n{'='*60}")
    print(f"🧪 TESTING: {command}")
    print(f"{'='*60}")
    child.sendline(command)
    start = time.time()

    while True:
        try:
            # Wait for either a prompt or a question
            index = child.expect([
                r'Execute tasks\?.*\[y/n',  # Task execution prompt
                r'You[\x00-\x7F]*:',         # Regular prompt
            ], timeout=timeout)

            elapsed = time.time() - start

            if index == 0:  # Execute tasks prompt
                print(f"\n💬 Rozet asks: Execute tasks?")
                if auto_confirm:
                    print(f"🤖 Responding: y")
                    child.sendline('y')
                    # Continue waiting for next prompt
                else:
                    print(f"🤖 Responding: n")
                    child.sendline('n')
                    return True
            elif index == 1:  # Regular You: prompt
                print(f"\n⏱️  Total response time: {elapsed:.1f}s")
                return True

        except pexpect.TIMEOUT:
            elapsed = time.time() - start
            print(f"\n⚠️  TIMEOUT after {elapsed:.1f}s")
            print(f"Last output:\n{child.before}")
            return False

def main():
    print("\n" + "="*70)
    print("🤖 ROZET TESTING ITSELF")
    print("Using Rozet to analyze and improve Rozet")
    print("="*70 + "\n")

    # Ensure we run from project root so run.sh can source helpers
    os.chdir(ROOT)

    # Start REPL
    print("Starting rozet --repl...")
    child = pexpect.spawn(
        "./run.sh --repl",
        cwd=str(ROOT),
        timeout=120,
        encoding="utf-8",
    )
    child.logfile = sys.stdout

    try:
        # Wait for startup
        print("Waiting for startup...")
        child.expect(r'You[\x00-\x7F]*:', timeout=60)
        print("\n✅ REPL started!\n")

        # Test 1: Ask Rozet to analyze its own codebase
        print("\n🎯 TEST 1: Self-analysis of error handling")
        send_and_wait(child, "analyze the orchestrator/tui.py file and identify any error handling issues", 300)

        # Test 2: Ask Rozet to fix the 401 error
        print("\n🎯 TEST 2: Fix the 401 authentication error")
        send_and_wait(child, "I'm getting a 401 'User not found' error when using the REPL. Can you find and fix this issue?", 300)

        # Test 3: Simple file creation to test basic functionality
        print("\n🎯 TEST 3: Basic file creation")
        send_and_wait(child, "create a file called test.txt with the text 'Hello from Rozet'", 180)

        # Clean exit
        print("\n" + "="*60)
        print("Exiting...")
        child.sendline('exit')
        child.expect(pexpect.EOF, timeout=10)
        print("\n✅ Test complete!")

    except pexpect.TIMEOUT as e:
        print(f"\n❌ TIMEOUT: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        if child.isalive():
            child.close()

if __name__ == '__main__':
    main()
