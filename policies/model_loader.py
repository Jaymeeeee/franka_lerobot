"""LeRobot policy loading helpers."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.policies.factory import make_pre_post_processors
from lerobot.utils.constants import ACTION


@dataclass
class LoadedPolicy:
    policy: ACTPolicy
    preprocessor: object
    postprocessor: object
    device: torch.device
    state_dim: int
    action_dim: int
    image_keys: list[str]

# TODO: 看看这里能不能做到统一模型加载
def load_act_policy(policy_path: str, device_override: str = "") -> LoadedPolicy:
    policy = ACTPolicy.from_pretrained(policy_path)
    if device_override:
        policy.config.device = device_override
    device = torch.device(policy.config.device)
    policy.to(device)
    policy.eval()
    policy.reset()
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=policy.config,
        pretrained_path=policy_path,
        preprocessor_overrides={"device_processor": {"device": str(device)}},
    )
    # 这里的 image_keys 是 policy.config.image_features.keys()，需要从config中获取; 对应的是 config 的 input_features 中 type 是 VISUAL 的 key
    return LoadedPolicy(
        policy=policy,
        preprocessor=preprocessor,
        postprocessor=postprocessor,
        device=device,
        state_dim=int(policy.config.robot_state_feature.shape[0]),
        action_dim=int(policy.config.output_features[ACTION].shape[0]),
        image_keys=list(policy.config.image_features.keys()),
    )

