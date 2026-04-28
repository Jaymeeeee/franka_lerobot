"""
lerobot_policy.py

TODO:
- 封装 LeRobot 策略模型的统一调用接口。
- 提供 `predict(observation)` 的标准方法，输出结构化 action。
- 管理设备放置（CPU/GPU）、精度模式与推理上下文。
- 处理模型输入输出的 schema 对齐与版本兼容。
- 暴露推理耗时、模型状态等可观测指标。
"""

