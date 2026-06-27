"""Shared mixins for resource-sensitive workers."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator


_GPU_RESOURCE_LOCK: Any | None = None


def set_gpu_resource_lock(lock: Any | None) -> None:
    """Register the process-local lock used to serialize GPU-heavy tasks."""
    global _GPU_RESOURCE_LOCK
    _GPU_RESOURCE_LOCK = lock


def get_gpu_resource_lock() -> Any | None:
    return _GPU_RESOURCE_LOCK


class GPUResourceMixin:
    """Strict mutex helper for CUDA/NVENC tasks.

    The lock is process-local but can wrap a multiprocessing semaphore passed by
    the parent process. CUDA cache cleanup runs before releasing the lock so the
    next task never starts with stale VRAM pressure from the previous task.
    """

    @contextmanager
    def gpu_resource(self, *, cleanup: bool = True) -> Iterator[None]:
        lock = self._gpu_resource_lock()
        acquired = False
        if lock is not None:
            lock.acquire()
            acquired = True
        try:
            self._ensure_gpu_memory_available()
            yield
        finally:
            if cleanup:
                self._clear_cuda_cache()
            if acquired:
                lock.release()

    def _gpu_resource_lock(self) -> Any | None:
        return get_gpu_resource_lock()

    def _ensure_gpu_memory_available(self) -> None:
        try:
            from core.vram_guardian import ensure_vram_available

            ensure_vram_available(task_name=self.__class__.__name__)
        except ImportError:
            return

    @staticmethod
    def uses_cuda_device(device: str) -> bool:
        return (device or "").strip().lower() == "cuda"

    @staticmethod
    def uses_gpu_codec(codec: str) -> bool:
        return "nvenc" in (codec or "").strip().lower()

    @staticmethod
    def _clear_cuda_cache() -> None:
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:  # noqa: BLE001
            return
