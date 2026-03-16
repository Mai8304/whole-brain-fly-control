from __future__ import annotations

from typing import Any

import numpy as np


def probe_walk_imitation(
    *,
    env_factory: object | None = None,
    action_dim: int = 59,
) -> dict[str, Any]:
    factory = env_factory or require_flybody_walk_env_factory()
    env = factory()
    reset_timestep = getattr(env, "reset")()
    step_timestep = getattr(env, "step")(np.zeros(action_dim, dtype=float))

    return {
        "status": "ok",
        "action_dim": action_dim,
        "reset_observation_keys": _extract_observation_keys(reset_timestep),
        "step_reward": float(getattr(step_timestep, "reward", 0.0) or 0.0),
    }


def require_flybody_walk_env_factory() -> object:
    try:
        from flybody.fly_envs import walk_imitation
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "flybody is not installed in the current environment. Run the probe from the dedicated flybody environment."
        ) from exc
    return walk_imitation


def _extract_observation_keys(timestep: Any) -> list[str]:
    observation = getattr(timestep, "observation", None)
    if isinstance(observation, dict):
        return sorted(str(key) for key in observation)
    return []
