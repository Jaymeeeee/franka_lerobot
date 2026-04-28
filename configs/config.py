"""Class-based deployment configuration."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RobotConfig:
    ip: str = "192.168.2.2"
    relative_dynamics: float = 0.05


@dataclass
class CameraConfig:
    image_discover_sec: float = 2.0
    image_topics: tuple[str, ...] = (
        "/cam1/cam1/color/image_raw",
        "/cam1/cam1/depth/image_rect_raw",
        "/cam2/cam2/color/image_raw",
        "/cam2/cam2/depth/image_rect_raw",
    )


@dataclass
class PolicyConfig:
    path: str = (
        "/home/wangyuxuan/franka_ws/models/pick_and_place/act_onlyjoint100/checkpoints/400000/"
        "pretrained_model"
    )
    device_override: str = ""
    state_source: str = "joint_positions"
    allow_state_padding: bool = True


@dataclass
class ControlConfig:
    hz: float = 10.0
    gripper_open_joint_pos: float = 0.04
    gripper_closed_joint_pos: float = 0.0
    gripper_action_threshold: float = 0.5


@dataclass
class Config:
    robot: RobotConfig = field(default_factory=RobotConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    control: ControlConfig = field(default_factory=ControlConfig)

