"""Build policy observation batches."""

from __future__ import annotations

from typing import Dict, List

import torch
from lerobot.utils.constants import OBS_STATE

from obs.state_processor import build_state
from ros2_bridge.camera_listener import CameraListener


class ObsBuilder:
    """Build raw observation dict consumed by lerobot preprocessors."""

    def __init__(
        self,
        device: torch.device,
        image_keys: List[str],
        state_dim: int,
        state_source: str = "joint_positions",
        allow_state_padding: bool = True,
    ):
        self._device = device
        self._image_keys = image_keys
        self._state_dim = state_dim
        self._state_source = state_source
        self._allow_state_padding = allow_state_padding

    def build(self, camera_listener: CameraListener, controller) -> Dict[str, torch.Tensor]:
        imgs = camera_listener.get_latest()
        if any(imgs.get(k) is None for k in self._image_keys):
            miss = [k for k in self._image_keys if imgs.get(k) is None]
            raise RuntimeError(f"Missing images: {miss}")

        batch: Dict[str, torch.Tensor] = {
            OBS_STATE: torch.from_numpy(
                build_state(
                    controller=controller,
                    target_dim=self._state_dim,
                    state_source=self._state_source,
                    allow_padding=self._allow_state_padding,
                )
            )
            .unsqueeze(0)
            .to(self._device),
        }
        for key in self._image_keys:
            rgb = imgs[key]
            t = torch.from_numpy(rgb).permute(2, 0, 1).contiguous().float().unsqueeze(0) / 255.0
            batch[key] = t.to(self._device)
        return batch

