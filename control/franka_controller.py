"""Franky-based FR3 arm and gripper controller."""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, Optional

import numpy as np
from franky import (
    Gripper,
    JointState as FrankyJointState,
    JointWaypoint,
    JointWaypointMotion,
    ReferenceType,
    Robot,
)

from control.base_controller import BaseController

_LOG = logging.getLogger(__name__)


class FrankyArmController(BaseController):
    N_ARM_JOINTS = 7

    def __init__(self, robot_ip: str, relative_dynamics_factor: float = 0.05):
        self._robot = Robot(robot_ip)
        self._robot.recover_from_errors()
        self._robot.relative_dynamics_factor = relative_dynamics_factor
        self._robot_lock = threading.Lock()
        self._gripper_lock = threading.Lock()
        try:
            self.gripper = Gripper(robot_ip)
        except Exception:  # pylint: disable=broad-except
            self.gripper = None
        self._last_gripper_width_m: float | None = None

    def move_joint_positions(self, q7: np.ndarray) -> None:
        q = [float(v) for v in q7.reshape(-1)[: self.N_ARM_JOINTS]]
        if len(q) != self.N_ARM_JOINTS:
            raise ValueError(f"Need 7 arm joints, got {len(q)}")
        motion = JointWaypointMotion(
            [JointWaypoint(target=FrankyJointState(position=q), reference_type=ReferenceType.Absolute)]
        )
        with self._robot_lock:
            self._robot.move(motion, asynchronous=True)

    def move_gripper_width(self, width_m: float, speed: float = 0.08) -> bool:
        if self.gripper is None:
            return False
        w = float(np.clip(width_m, 0.0, 0.1))
        if self._last_gripper_width_m is not None and abs(self._last_gripper_width_m - w) < 1e-4:
            return True
        try:
            with self._gripper_lock:
                self.gripper.move(w, speed)
            self._last_gripper_width_m = w
            return True
        except Exception as exc:  # pylint: disable=broad-except
            _LOG.warning("gripper move failed (%s): %s", type(exc).__name__, exc)
            return False

    def read_state_snapshot(self) -> Optional[Dict[str, Any]]:
        try:
            with self._robot_lock:
                st = self._robot.state
                _t = st.time
                _dur = _t() if callable(_t) else _t
                fci_sec = float(_dur.to_sec())
                q = np.asarray(st.q, dtype=float).reshape(-1).copy()
                dq = np.asarray(st.dq, dtype=float).reshape(-1).copy()
                aff = st.O_T_EE
                trans = np.asarray(aff.translation, dtype=float).reshape(-1).copy()
                quat = np.asarray(aff.quaternion, dtype=float).reshape(-1).copy()
        except Exception:  # pylint: disable=broad-except
            return None
        if q.size != 7 or dq.size != 7:
            return None
        return {
            "fci_sec": fci_sec,
            "joint_positions": q,
            "joint_velocities": dq,
            "translation": trans,
            "quaternion": quat,
        }

    def send_action(self, action: np.ndarray) -> None:
        self.move_joint_positions(action[:7])

