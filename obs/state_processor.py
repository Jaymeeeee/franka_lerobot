"""State processing helpers."""

from __future__ import annotations

import numpy as np

from control.base_controller import BaseController


def build_state(
    controller: BaseController,
    target_dim: int,
    state_source: str = "joint_positions",
    allow_padding: bool = True,
) -> np.ndarray:
    """Read and adapt state vector to target dimension."""
    snap = controller.read_state_snapshot()
    if snap is None:
        raise RuntimeError("read_state_snapshot() failed (robot state unavailable)")
    if state_source not in snap:
        raise RuntimeError(f"state source '{state_source}' not found in snapshot")

    raw = np.asarray(snap[state_source], dtype=np.float32).reshape(-1)
    if raw.size >= target_dim:
        return raw[:target_dim]
    if not allow_padding:
        raise RuntimeError(
            f"State dim mismatch: source '{state_source}' has {raw.size}, target needs {target_dim}"
        )
    padded = np.zeros((target_dim,), dtype=np.float32)
    padded[: raw.size] = raw
    return padded

