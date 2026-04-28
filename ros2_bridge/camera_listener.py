"""ROS2 camera utilities and listener."""

from __future__ import annotations

from functools import partial
from typing import Dict, Optional

import numpy as np
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy
from rclpy.qos import QoSProfile
from rclpy.qos import QoSPresetProfiles
from rclpy.qos import QoSReliabilityPolicy
from sensor_msgs.msg import Image


def clone_qos(q: QoSProfile) -> QoSProfile:
    return QoSProfile(
        history=q.history,
        depth=q.depth,
        reliability=q.reliability,
        durability=q.durability,
        lifespan=q.lifespan,
        deadline=q.deadline,
        liveliness=q.liveliness,
        liveliness_lease_duration=q.liveliness_lease_duration,
        avoid_ros_namespace_conventions=q.avoid_ros_namespace_conventions,
    )


def choose_qos_for_image_topic(node: Node, topic_name: str) -> QoSProfile:
    """Choose subscriber QoS based on existing publishers."""
    qos_profile = clone_qos(QoSPresetProfiles.get_from_short_key("sensor_data"))
    pubs_info = node.get_publishers_info_by_topic(topic_name)
    if not pubs_info:
        return qos_profile
    reliable_n = sum(
        1 for info in pubs_info if info.qos_profile.reliability == QoSReliabilityPolicy.RELIABLE
    )
    transient_local_n = sum(
        1 for info in pubs_info if info.qos_profile.durability == QoSDurabilityPolicy.TRANSIENT_LOCAL
    )
    n = len(pubs_info)
    qos_profile.reliability = (
        QoSReliabilityPolicy.RELIABLE if reliable_n == n else QoSReliabilityPolicy.BEST_EFFORT
    )
    qos_profile.durability = (
        QoSDurabilityPolicy.TRANSIENT_LOCAL if transient_local_n == n else QoSDurabilityPolicy.VOLATILE
    )
    return qos_profile


def ros_image_to_rgb_u8(msg: Image) -> np.ndarray:
    """Convert ROS image to RGB uint8 without cv_bridge."""
    h, w = int(msg.height), int(msg.width)
    if h <= 0 or w <= 0:
        raise ValueError("invalid image size")
    enc = (msg.encoding or "").lower()
    step = int(msg.step)
    data = memoryview(msg.data)

    def rows_u8(cpp: int) -> np.ndarray:
        need = h * step
        if len(data) < need:
            raise ValueError(f"image data too short: need {need}, got {len(data)}")
        raw = np.frombuffer(data, dtype=np.uint8, count=need)
        view = raw.reshape((h, step))
        row_w = w * cpp
        if row_w > step:
            raise ValueError("step too small for width and channels")
        return view[:, :row_w].reshape((h, w, cpp)).copy()

    if enc == "bgr8":
        bgr = rows_u8(3)
        return bgr[:, :, ::-1]
    if enc == "rgb8":
        return rows_u8(3)
    if enc in ("mono8", "8uc1"):
        gray = rows_u8(1)[:, :, 0]
        return np.stack([gray, gray, gray], axis=-1)
    if enc in ("16uc1",):
        need = h * step
        if len(data) < need:
            raise ValueError(f"depth data too short: need {need}, got {len(data)}")
        if w * 2 > step:
            raise ValueError("16UC1 step too small for width")
        d = np.empty((h, w), dtype=np.float32)
        for row in range(h):
            ro = row * step
            d[row] = np.frombuffer(data[ro : ro + w * 2], dtype="<u2", count=w)
        valid = d > 0
        dmax = max(float(np.percentile(d[valid], 99.0)), 1.0) if valid.any() else 1.0
        g = np.clip(d / dmax * 255.0, 0.0, 255.0).astype(np.uint8)
        return np.stack([g, g, g], axis=-1)

    raise ValueError(f"unsupported image encoding: {msg.encoding!r}")


class CameraListener:
    """Subscribe image topics and keep latest RGB frames by key."""

    def __init__(self, node: Node, image_map: Dict[str, str]):
        self._node = node
        self._image_map = image_map
        self._images: Dict[str, np.ndarray] = {}
        self._subscriptions = []
        for key, topic in image_map.items():
            qos = choose_qos_for_image_topic(node, topic)
            sub = node.create_subscription(Image, topic, partial(self._img_cb, key), qos)
            self._subscriptions.append(sub)
            node.get_logger().info(
                f"{key} <- {topic} (qos rel={qos.reliability.name} dur={qos.durability.name})"
            )

    def _img_cb(self, key: str, msg: Image) -> None:
        try:
            self._images[key] = ros_image_to_rgb_u8(msg)
        except Exception as exc:  # pylint: disable=broad-except
            self._node.get_logger().warning(f"image convert failed {key}: {exc}")

    def get_latest(self) -> Dict[str, Optional[np.ndarray]]:
        return {key: self._images.get(key) for key in self._image_map.keys()}

