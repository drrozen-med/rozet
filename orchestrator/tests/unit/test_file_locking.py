"""Unit tests for file locking mechanism (TDD - tests first)."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from threading import Thread
from unittest.mock import Mock, patch

import pytest

from orchestrator.core.file_locking import FileLockManager, LockTimeoutError


class TestFileLockManager:
    """Test file locking for concurrent access."""
    
    def test_lock_acquire_release(self, tmp_path: Path):
        """Test basic lock acquire and release."""
        lock_manager = FileLockManager()
        test_file = tmp_path / "test.txt"
        test_file.write_text("initial")
        
        # Acquire lock
        lock = lock_manager.acquire_lock(str(test_file), timeout=1.0)
        assert lock is not None
        assert lock_manager.is_locked(str(test_file))
        
        # Release lock
        lock_manager.release_lock(str(test_file))
        assert not lock_manager.is_locked(str(test_file))
    
    def test_lock_timeout(self, tmp_path: Path):
        """Test that acquiring a lock on an already-locked file times out."""
        lock_manager = FileLockManager()
        test_file = tmp_path / "test.txt"
        test_file.write_text("initial")
        
        # Acquire first lock
        lock1 = lock_manager.acquire_lock(str(test_file), timeout=1.0)
        assert lock1 is not None
        
        # Try to acquire second lock (should timeout)
        with pytest.raises(LockTimeoutError):
            lock_manager.acquire_lock(str(test_file), timeout=0.1)
        
        # Release first lock
        lock_manager.release_lock(str(test_file))
        
        # Now should be able to acquire
        lock2 = lock_manager.acquire_lock(str(test_file), timeout=1.0)
        assert lock2 is not None
        lock_manager.release_lock(str(test_file))
    
    def test_concurrent_access(self, tmp_path: Path):
        """Test that locks prevent concurrent file modifications."""
        lock_manager = FileLockManager()
        test_file = tmp_path / "concurrent.txt"
        test_file.write_text("0")
        
        results = []
        errors = []
        
        def write_with_lock(thread_id: int, value: str):
            """Write to file with lock."""
            try:
                lock = lock_manager.acquire_lock(str(test_file), timeout=2.0)
                time.sleep(0.1)  # Simulate work
                test_file.write_text(value)
                results.append((thread_id, value))
                lock_manager.release_lock(str(test_file))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Start 3 threads trying to write concurrently
        threads = [
            Thread(target=write_with_lock, args=(i, f"value_{i}"))
            for i in range(3)
        ]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # Should have no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"
        
        # File should have final value (one of the writes)
        final_content = test_file.read_text()
        assert final_content in ["value_0", "value_1", "value_2"]
        
        # All writes should have completed
        assert len(results) == 3
    
    def test_context_manager(self, tmp_path: Path):
        """Test using FileLockManager as context manager."""
        lock_manager = FileLockManager()
        test_file = tmp_path / "context.txt"
        test_file.write_text("initial")
        
        with lock_manager.lock(str(test_file), timeout=1.0):
            assert lock_manager.is_locked(str(test_file))
            test_file.write_text("modified")
        
        # Lock should be released after context exit
        assert not lock_manager.is_locked(str(test_file))
        assert test_file.read_text() == "modified"
    
    def test_nested_locks_same_file(self, tmp_path: Path):
        """Test that nested locks on same file fail."""
        lock_manager = FileLockManager()
        test_file = tmp_path / "nested.txt"
        test_file.write_text("initial")
        
        with lock_manager.lock(str(test_file), timeout=1.0):
            with pytest.raises(LockTimeoutError):
                with lock_manager.lock(str(test_file), timeout=0.1):
                    pass
    
    def test_different_files_no_conflict(self, tmp_path: Path):
        """Test that locks on different files don't conflict."""
        lock_manager = FileLockManager()
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("1")
        file2.write_text("2")
        
        with lock_manager.lock(str(file1), timeout=1.0):
            with lock_manager.lock(str(file2), timeout=1.0):
                assert lock_manager.is_locked(str(file1))
                assert lock_manager.is_locked(str(file2))
        
        assert not lock_manager.is_locked(str(file1))
        assert not lock_manager.is_locked(str(file2))
    
    def test_lock_cleanup_on_error(self, tmp_path: Path):
        """Test that locks are released even if exception occurs."""
        lock_manager = FileLockManager()
        test_file = tmp_path / "error.txt"
        test_file.write_text("initial")
        
        try:
            with lock_manager.lock(str(test_file), timeout=1.0):
                assert lock_manager.is_locked(str(test_file))
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Lock should be released despite error
        assert not lock_manager.is_locked(str(test_file))
    
    def test_lock_expiry(self, tmp_path: Path):
        """Test that locks expire after timeout period."""
        lock_manager = FileLockManager()
        test_file = tmp_path / "expiry.txt"
        test_file.write_text("initial")
        
        # Acquire lock with short expiry
        lock = lock_manager.acquire_lock(str(test_file), timeout=0.5, expiry=0.2)
        assert lock is not None
        
        # Wait for expiry
        time.sleep(0.3)
        
        # Should be able to acquire new lock (old one expired)
        lock2 = lock_manager.acquire_lock(str(test_file), timeout=1.0)
        assert lock2 is not None
        lock_manager.release_lock(str(test_file))

