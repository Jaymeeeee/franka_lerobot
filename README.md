# franka_lerobot

Use for control franka by lerobot

## 框架

### 最小可行框架

franka_lerobot/
├── ros2_bridge/
├── obs/
├── policies/
├── control/
├── utils/
├── configs/
├── scripts/

### 完整框架

franka_lerobot/
├── configs/
├── ros2_bridge/
├── modules/
├── policies/
├── obs/
├── control/
├── utils/
├── scripts/
├── launch/
├── requirements.txt / pyproject.toml

### 各模块作用

ros2_bridge/
├── obs_subscriber.py
├── action_publisher.py
├── camera_listener.py
├── robot_state_listener.py

obs/
├── obs_builder.py
├── image_processor.py
├── state_processor.py
├── sync.py

policies/
├── lerobot_policy.py
├── policy_wrapper.py
├── model_loader.py
├── inference.py

control/
├── base_controller.py
├── franka_controller.py
├── moveit_controller.py
├── gripper_controller.py

utils/
├── transforms.py
├── normalization.py
├── timer.py
├── logger.py

configs/
├── robot.yaml
├── camera.yaml
├── policy.yaml
├── control.yaml

## 数据流

ROS2 topics
     ↓
ros2_bridge
     ↓
Observation dict
     ↓
obs module
     ↓
policy (LeRobot)
     ↓
action dict
     ↓
control module
     ↓
Franka robot

## Topic 命名规范（草案）

统一前缀：`/franka_lerobot`

- 输入观测相关
  - `/franka_lerobot/in/robot/joint_state`：机械臂关节状态（来自机器人驱动）
  - `/franka_lerobot/in/robot/ee_state`：末端位姿/速度状态
  - `/franka_lerobot/in/end_effector/state`：末端执行器状态（gripper 或 dexterous hand）
  - `/franka_lerobot/in/camera/rgb`：RGB 图像
  - `/franka_lerobot/in/camera/depth`：Depth 图像（可选）
- 融合观测与推理输出
  - `/franka_lerobot/obs`：融合后的 Observation（供 policy 订阅）
  - `/franka_lerobot/action`：policy 输出动作（供控制器订阅）
- 系统状态
  - `/franka_lerobot/status/heartbeat`：节点心跳
  - `/franka_lerobot/status/error`：错误告警

建议命名规则：

- 输入统一放在 `/in/...`，中间产物用 `/obs`，输出动作用 `/action`
- 状态与告警统一放在 `/status/...`
- 多相机场景扩展：`/franka_lerobot/in/camera/<camera_name>/rgb|depth`

## Observation / Action 字段表（草案）

### Observation（发布到 `/franka_lerobot/obs`）

- `header.stamp` (`builtin_interfaces/Time`)：融合时间戳
- `header.frame_id` (`string`)：参考坐标系，如 `panda_link0`
- `robot.joint.position` (`float[]`)：关节位置
- `robot.joint.velocity` (`float[]`)：关节速度
- `robot.joint.effort` (`float[]`, optional)：关节力矩
- `robot.ee.pose` (`float[7]`)：末端位姿 `[x,y,z,qx,qy,qz,qw]`
- `robot.ee.twist` (`float[6]`, optional)：末端速度 `[vx,vy,vz,wx,wy,wz]`
- `end_effector.type` (`string`)：`gripper` 或 `dexterous_hand`
- `end_effector.state` (`float[]`)：夹爪开合或灵巧手关节状态
- `image.rgb` (`sensor_msgs/Image`)：RGB 图像
- `image.depth` (`sensor_msgs/Image`, optional)：深度图
- `meta.valid_mask` (`bool[]`)：关键字段可用性标记
- `meta.source_latency_ms` (`float`)：从采集到融合的延迟

### Action（发布到 `/franka_lerobot/action`）

- `header.stamp` (`builtin_interfaces/Time`)：动作生成时间
- `header.frame_id` (`string`)：动作参考坐标系
- `arm.mode` (`string`)：`joint` / `cartesian`
- `arm.command` (`float[]`)：机械臂动作向量（维度由配置定义）
- `end_effector.command` (`float[]`)：末端执行器动作向量
- `control.horizon` (`float`, optional)：控制时间窗（秒）
- `control.confidence` (`float`, optional)：policy 输出置信度

## 节点图（发布/订阅、频率、QoS）

### 1) 感知与状态输入节点（外部节点）

- 机器人驱动节点
  - 发布：`/franka_lerobot/in/robot/joint_state`（100Hz，QoS: reliable, keep_last=10）
  - 发布：`/franka_lerobot/in/robot/ee_state`（100Hz，QoS: reliable, keep_last=10）
- 末端执行器节点（gripper / dexterous hand）
  - 发布：`/franka_lerobot/in/end_effector/state`（30~100Hz，QoS: reliable, keep_last=10）
- 相机节点
  - 发布：`/franka_lerobot/in/camera/rgb`（30Hz，QoS: best_effort, keep_last=5）
  - 发布：`/franka_lerobot/in/camera/depth`（30Hz，可选，QoS: best_effort, keep_last=5）

### 2) `obs_builder` 节点

- 订阅：
  - `/franka_lerobot/in/robot/joint_state`
  - `/franka_lerobot/in/robot/ee_state`
  - `/franka_lerobot/in/end_effector/state`
  - `/franka_lerobot/in/camera/rgb`
  - `/franka_lerobot/in/camera/depth`（可选）
- 发布：
  - `/franka_lerobot/obs`（建议 20~30Hz，QoS: reliable, keep_last=10）
  - `/franka_lerobot/status/heartbeat`（1Hz，QoS: reliable, keep_last=3）
  - `/franka_lerobot/status/error`（事件触发，QoS: reliable, keep_last=50）

### 3) `policy_node` 节点

- 订阅：
  - `/franka_lerobot/obs`（QoS: reliable, keep_last=10）
- 发布：
  - `/franka_lerobot/action`（与推理频率一致，建议 10~30Hz，QoS: reliable, keep_last=10）
  - `/franka_lerobot/status/heartbeat`（1Hz）
  - `/franka_lerobot/status/error`（事件触发）

### 4) `controller_node` 节点（两种后端）

- 订阅：
  - `/franka_lerobot/action`（QoS: reliable, keep_last=10）
- 后端 A：纯 ROS2 控制（直接发布到驱动控制 topic）
- 后端 B：MoveIt 控制机械臂 + Franky 控制夹爪
- 发布：
  - `/franka_lerobot/status/heartbeat`（1Hz）
  - `/franka_lerobot/status/error`（事件触发）

## 故障策略（先定义，后实现）

说明：本节先定义系统行为规范，当前阶段可先不实现自动恢复逻辑，但建议保留日志与告警出口。

### 1) 相机掉线（RGB 或 Depth）

- 判定条件：
  - 连续 `N` 个预期周期未收到图像（建议 `N=3`）
  - 或图像时间戳与当前时间差超过阈值（建议 `>150ms`）
- 系统行为（规范）：
  - 仅 depth 掉线：允许降级为 RGB-only 推理（若模型支持）
  - RGB 掉线：停止 policy 新动作输出，切换为 hold-last（短时）后安全停机
  - 发布 `status/error` 告警，错误码如 `CAMERA_TIMEOUT`

### 2) 手爪/灵巧手无反馈

- 判定条件：
  - `end_effector/state` 在超时时间内无更新（建议 `>100ms`）
- 系统行为（规范）：
  - 机械臂与末端解耦：可选“仅冻结末端动作，机械臂继续”或“全系统暂停”
  - 默认建议：真机阶段使用“全系统暂停”更安全
  - 发布 `status/error` 告警，错误码如 `EE_STATE_TIMEOUT`

### 3) policy 推理超时

- 判定条件：
  - 单次推理耗时超过控制周期预算（例如控制 20Hz 时预算 50ms）
  - 连续超时次数超过阈值（建议 `>=3`）
- 系统行为（规范）：
  - 短时超时：允许一次 hold-last action
  - 连续超时：控制器进入安全模式（减速/停止），拒绝继续下发新动作
  - 发布 `status/error` 告警，错误码如 `POLICY_TIMEOUT`

### 4) 通用故障处理等级

- `WARN`：可降级运行（例如 depth 丢失）
- `ERROR`：需要暂停模块并人工确认（例如 policy 连续超时）
- `FATAL`：立即停机（例如关键状态流全部丢失、控制指令异常越界）

### 5) 建议最小落地顺序

1. 先统一错误码和 `status/error` 消息格式
2. 再实现超时检测与日志（不自动恢复）
3. 最后实现自动降级、hold-last、安全停机策略