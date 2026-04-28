"""Controller interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import numpy as np


class BaseController(ABC):
    """Abstract robot controller."""

    @abstractmethod
    def send_action(self, action: np.ndarray) -> None:
        """Send one action vector to robot."""

    @abstractmethod
    def read_state_snapshot(self) -> Optional[Dict[str, Any]]:
        """Read current robot state snapshot."""

