"""
action_publisher.py

TODO:
- 实现动作发布端，将 policy 输出发布到 `/franka_lerobot/action`。
- 支持统一 Action schema 的打包与字段检查（arm/end_effector/control）。
- 配置并应用可靠传输 QoS（reliable + keep_last）。
- 记录发布频率、延迟与失败次数等运行指标。
- 在动作非法或发布失败时上报错误码与诊断信息。
"""

