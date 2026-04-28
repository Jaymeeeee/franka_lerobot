"""
logger.py

TODO:
- 提供项目统一日志接口（控制台 + 文件 + ROS2 日志适配）。
- 支持结构化日志字段（module, topic, error_code, latency）。
- 定义日志级别规范（DEBUG/INFO/WARN/ERROR/FATAL）。
- 提供故障策略相关错误码输出辅助函数。
- 预留与运行监控系统对接能力（如后续 metrics exporter）。
"""

