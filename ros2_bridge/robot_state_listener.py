"""
robot_state_listener.py

TODO:
- 订阅机械臂关节状态、末端状态和末端执行器状态输入 topic。
- 把 joint/ee/end_effector 状态转为统一内部数据结构。
- 校验维度、单位和时间戳新鲜度，过滤明显异常数据。
- 提供线程安全的最新状态访问接口给 obs_builder。
- 在状态超时或反馈缺失时触发标准错误事件。
"""

