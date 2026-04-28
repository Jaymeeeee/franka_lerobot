"""
obs_subscriber.py

TODO:
- 实现 Observation 订阅端（主要给 policy 节点使用）。
- 对接统一的 `/franka_lerobot/obs` topic 与 QoS 配置。
- 提供消息反序列化与基础字段校验（时间戳、frame_id、关键状态完整性）。
- 对外暴露回调接口，供 preprocess/inference 流水线接入。
- 在订阅异常或超时时发布标准化错误事件（后续接 status/error）。
"""

