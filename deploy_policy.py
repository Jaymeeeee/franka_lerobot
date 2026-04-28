#!/usr/bin/env python3
"""Entrypoint for policy deployment node."""

from __future__ import annotations

import sys

import rclpy

from configs.config import Config
from modules.deploy_node import DeployNode


def main() -> None:
    rclpy.init()
    node = DeployNode(Config())
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
