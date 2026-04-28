"""Composable deploy node split from original single-file script."""

from __future__ import annotations

import time

import numpy as np
import rclpy
from rclpy.node import Node

from configs.config import Config
from control.franka_controller import FrankyArmController
from obs.obs_builder import ObsBuilder
from policies.model_loader import load_act_policy
from policies.policy_wrapper import PolicyWrapper
from ros2_bridge.camera_listener import CameraListener


class DeployNode(Node):
    """Runtime deploy node with same behavior as the old script."""

    def __init__(self, cfg: Config):
        super().__init__("act_deploy_minimal")
        self._cfg = cfg

        # ros2 图像发布端发现和 Qos 预热等待
        if cfg.camera.image_discover_sec > 0:
            self.get_logger().info(
                f"DDS discover wait {cfg.camera.image_discover_sec:.1f}s for image QoS..."
            )
            t_end = time.monotonic() + cfg.camera.image_discover_sec
            while time.monotonic() < t_end and rclpy.ok():
                rclpy.spin_once(self, timeout_sec=0.05)

        self.get_logger().info(f"Loading ACT from {cfg.policy.path}")
        loaded = load_act_policy(cfg.policy.path, cfg.policy.device_override)
        self.policy = loaded.policy
        self._action_dim = loaded.action_dim
        if len(loaded.image_keys) != len(cfg.camera.image_topics):
            raise ValueError(
                f"image key/topic size mismatch: keys={len(loaded.image_keys)} topics={len(cfg.camera.image_topics)}"
            )

        image_map = {k: t for k, t in zip(loaded.image_keys, cfg.camera.image_topics)}
        self.camera_listener = CameraListener(self, image_map)
        self.controller = FrankyArmController(cfg.robot.ip, cfg.robot.relative_dynamics)
        self._arm_dim = int(getattr(self.controller, "N_ARM_JOINTS", 7))
        if self._action_dim < self._arm_dim:
            raise ValueError(f"Expect action_dim>={self._arm_dim}, got {self._action_dim}")
        self.obs_builder = ObsBuilder(
            device=loaded.device,
            image_keys=loaded.image_keys,
            state_dim=loaded.state_dim,
            state_source=cfg.policy.state_source,
            allow_state_padding=cfg.policy.allow_state_padding,
        )
        self.policy_wrapper = PolicyWrapper(loaded.policy, loaded.preprocessor, loaded.postprocessor)
        self._last_gripper_fail_log_mono: float = 0.0

        self.create_timer(1.0 / cfg.control.hz, self._tick)
        self.get_logger().info("deploy node ready")

    def _tick(self) -> None:
        action = self.policy_wrapper.pop_action()
        if action is None:
            try:
                raw_obs = self.obs_builder.build(self.camera_listener, self.controller)
                self.policy_wrapper.refill_actions(raw_obs)
                action = self.policy_wrapper.pop_action()
            except Exception as exc:  # pylint: disable=broad-except
                self.get_logger().warning(f"skip tick: {exc}")
                return
        if action is None:
            return
        # 移动机械臂
        self.controller.move_joint_positions(action[: self._arm_dim])
        # 移动夹爪
        if (
            self.controller.gripper is not None
            and self._action_dim >= (self._arm_dim + 1)
            and action.shape[0] >= (self._arm_dim + 1)
        ):
            open_flag = float(action[self._arm_dim]) >= self._cfg.control.gripper_action_threshold
            finger_joint = (
                self._cfg.control.gripper_open_joint_pos
                if open_flag
                else self._cfg.control.gripper_closed_joint_pos
            )
            if not self.controller.move_gripper_width(2.0 * finger_joint):
                now = time.monotonic()
                if now - self._last_gripper_fail_log_mono > 5.0:
                    self._last_gripper_fail_log_mono = now
                    self.get_logger().warning("gripper command failed and ignored")
