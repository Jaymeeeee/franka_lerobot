"""Policy pipeline wrapper."""

from __future__ import annotations

from collections import deque

import numpy as np
import torch


class PolicyWrapper:
    """Queue-based action chunk wrapper for ACT-like policies."""

    def __init__(self, policy, preprocessor, postprocessor):
        self._policy = policy
        self._preprocessor = preprocessor
        self._postprocessor = postprocessor
        self._action_queue: deque[np.ndarray] = deque()

    def refill_actions(self, raw_obs: dict) -> None:
        processed = self._preprocessor(raw_obs)
        with torch.inference_mode():
            n = int(self._policy.config.n_action_steps)
            chunk = self._policy.predict_action_chunk(processed)[:, :n, :]
        post = self._postprocessor(chunk)
        if post.dim() == 3:
            post = post.squeeze(0)
        for i in range(post.shape[0]):
            self._action_queue.append(post[i].detach().cpu().numpy())

    def pop_action(self) -> np.ndarray | None:
        if not self._action_queue:
            return None
        return np.asarray(self._action_queue.popleft(), dtype=np.float64).reshape(-1)

