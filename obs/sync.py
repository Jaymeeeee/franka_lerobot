"""
sync.py

TODO:
- 提供多源数据同步策略：exact、approximate、latest+timeout。
- 统一管理各输入流时间戳对齐与窗口缓存。
- 输出同步质量指标（延迟、抖动、丢包率）。
- 对超时或对齐失败进行降级判定并返回原因码。
- 为 obs_builder 暴露简洁的 `get_synced_frame()` 接口。
"""

