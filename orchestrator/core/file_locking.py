"""File locking mechanism for multi-agent concurrent operations.

This module provides file-level locking to prevent race conditions when
multiple agents or workers access the same files concurrently.
"""

from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Optional

LOGGER = logging.getLogger(__name__)


class LockTimeoutError(Exception):
    """Raised when a file lock cannot be acquired within the timeout period."""
    
    def __init__(self, file_path: str, timeout: float):
        self.file_path = file_path
        self.timeout = timeout
        super().__init__(
            f"Could not acquire lock for {file_path} within {timeout}s"
        )


class FileLock:
    """Represents a file lock with expiry tracking."""
    
    def __init__(self, file_path: str, expiry: Optional[float] = None):
        self.file_path = file_path
        self.acquired_at = time.time()
        self.expiry = expiry
        self.lock = threading.Lock()
    
    def is_expired(self) -> bool:
        """Check if this lock has expired."""
        if self.expiry is None:
            return False
        return (time.time() - self.acquired_at) > self.expiry
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Lock release handled by FileLockManager
        pass


class FileLockManager:
    """Manages file locks for concurrent access control."""
    
    def __init__(self):
        self._locks: Dict[str, FileLock] = {}
        self._manager_lock = threading.Lock()
    
    def acquire_lock(
        self,
        file_path: str,
        timeout: float = 5.0,
        expiry: Optional[float] = None,
    ) -> Optional[FileLock]:
        """Acquire a lock on a file.
        
        Args:
            file_path: Path to the file to lock
            timeout: Maximum time to wait for lock (seconds)
            expiry: Optional lock expiry time (seconds). If None, lock doesn't expire.
        
        Returns:
            FileLock object if acquired, None if timeout
        
        Raises:
            LockTimeoutError: If lock cannot be acquired within timeout
        """
        normalized_path = str(Path(file_path).resolve())
        start_time = time.time()
        
        while True:
            with self._manager_lock:
                # Check if file is already locked
                existing_lock = self._locks.get(normalized_path)
                
                if existing_lock:
                    # Check if existing lock is expired
                    if existing_lock.is_expired():
                        LOGGER.debug(
                            "Removing expired lock for %s", normalized_path
                        )
                        del self._locks[normalized_path]
                        existing_lock = None
                
                if not existing_lock:
                    # Can acquire lock
                    new_lock = FileLock(normalized_path, expiry=expiry)
                    self._locks[normalized_path] = new_lock
                    LOGGER.debug("Acquired lock for %s", normalized_path)
                    return new_lock
            
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise LockTimeoutError(normalized_path, timeout)
            
            # Wait a bit before retrying
            time.sleep(0.01)
    
    def release_lock(self, file_path: str) -> None:
        """Release a lock on a file.
        
        Args:
            file_path: Path to the file to unlock
        """
        normalized_path = str(Path(file_path).resolve())
        
        with self._manager_lock:
            if normalized_path in self._locks:
                del self._locks[normalized_path]
                LOGGER.debug("Released lock for %s", normalized_path)
            else:
                LOGGER.warning(
                    "Attempted to release non-existent lock for %s",
                    normalized_path
                )
    
    def is_locked(self, file_path: str) -> bool:
        """Check if a file is currently locked.
        
        Args:
            file_path: Path to the file to check
        
        Returns:
            True if file is locked, False otherwise
        """
        normalized_path = str(Path(file_path).resolve())
        
        with self._manager_lock:
            lock = self._locks.get(normalized_path)
            if not lock:
                return False
            
            # Check if expired
            if lock.is_expired():
                del self._locks[normalized_path]
                return False
            
            return True
    
    @contextmanager
    def lock(self, file_path: str, timeout: float = 5.0, expiry: Optional[float] = None):
        """Context manager for file locking.
        
        Usage:
            with lock_manager.lock("file.txt"):
                # File is locked here
                pass
            # Lock is automatically released
        
        Args:
            file_path: Path to the file to lock
            timeout: Maximum time to wait for lock (seconds)
            expiry: Optional lock expiry time (seconds)
        
        Yields:
            FileLock object
        
        Raises:
            LockTimeoutError: If lock cannot be acquired within timeout
        """
        lock = None
        try:
            lock = self.acquire_lock(file_path, timeout=timeout, expiry=expiry)
            yield lock
        finally:
            if lock:
                self.release_lock(file_path)
    
    def cleanup_expired_locks(self) -> int:
        """Remove all expired locks.
        
        Returns:
            Number of locks removed
        """
        with self._manager_lock:
            expired_paths = [
                path
                for path, lock in self._locks.items()
                if lock.is_expired()
            ]
            
            for path in expired_paths:
                del self._locks[path]
                LOGGER.debug("Cleaned up expired lock for %s", path)
            
            return len(expired_paths)

