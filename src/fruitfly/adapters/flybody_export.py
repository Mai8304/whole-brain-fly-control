from __future__ import annotations

import math
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .flybody_obs import adapt_observation


def export_straight_walking_records(
    *,
    expert_source: object | None = None,
    episodes: int = 1,
    max_steps: int = 32,
    policy_dir: str | Path | None = None,
) -> list[dict[str, list[float]]]:
    source = expert_source or require_flybody_expert_source(policy_dir=policy_dir)
    rollout_records = getattr(source, "rollout")(episodes=episodes, max_steps=max_steps)

    exported: list[dict[str, list[float]]] = []
    for record in rollout_records:
        observation, command = adapt_straight_walking_inputs(record["observation"], record.get("command"))
        exported.append(
            {
                "observation": observation,
                "command": command,
                "expert_mean": _normalize_vector(record["expert_mean"]),
                "expert_log_std": _normalize_vector(record["expert_log_std"]),
                "episode_id": int(record.get("episode_id", 0)),
                "step_id": int(record.get("step_id", 0)),
                "task": str(record.get("task", "straight_walking")),
            }
        )
    return exported


def adapt_straight_walking_inputs(
    observation: Any,
    command: Any | None = None,
) -> tuple[list[float], list[float]]:
    normalized_observation = _normalize_observation(observation)
    normalized_command = _normalize_vector(command if command is not None else _extract_command(observation))
    return normalized_observation, normalized_command


def require_flybody_expert_source(*, policy_dir: str | Path | None = None) -> object:
    try:
        import flybody  # noqa: F401
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "flybody is not installed in the current environment. Run dataset export from a dedicated flybody environment."
        ) from exc

    resolved_policy_dir = _resolve_walking_policy_dir(policy_dir)
    return _SavedModelWalkingExpertSource(policy_dir=resolved_policy_dir)


def _normalize_observation(observation: Any) -> list[float]:
    if isinstance(observation, Mapping):
        if any(key in observation for key in ("proprio", "mechanosensation", "vision", "command")):
            return list(adapt_observation(observation))
        return _flatten_mapping_values(observation)
    return _normalize_vector(observation)


def _flatten_mapping_values(observation: Mapping[str, Any]) -> list[float]:
    flattened: list[float] = []
    for key in sorted(str(item) for item in observation.keys()):
        flattened.extend(_flatten_values(observation[key]))
    return flattened


def _flatten_values(values: Any) -> list[float]:
    if isinstance(values, Mapping):
        return _flatten_mapping_values(values)
    if hasattr(values, "tolist") and not isinstance(values, (str, bytes)):
        values = values.tolist()
    if isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
        flattened: list[float] = []
        for item in values:
            flattened.extend(_flatten_values(item))
        return flattened
    return [float(values)]


def _extract_command(observation: Any) -> Sequence[float]:
    if isinstance(observation, Mapping):
        if "command" in observation:
            return observation.get("command", [])
        ref_displacement = observation.get("walker/ref_displacement")
        flat_ref = _flatten_values(ref_displacement) if ref_displacement is not None else []
        if len(flat_ref) >= 2:
            return [float(flat_ref[0]), float(flat_ref[1])]
    return [1.0, 0.0]


def _resolve_walking_policy_dir(policy_dir: str | Path | None) -> Path:
    raw = policy_dir or os.environ.get("FLYBODY_TRAINED_POLICIES_DIR")
    if not raw:
        raise RuntimeError(
            "Walking policy directory is required. Pass --policy-dir or set FLYBODY_TRAINED_POLICIES_DIR."
        )
    base = Path(raw).expanduser().resolve()
    direct_model = base / "saved_model.pb"
    if direct_model.exists():
        return base
    nested_walking = base / "walking" / "saved_model.pb"
    if nested_walking.exists():
        return nested_walking.parent
    raise RuntimeError(f"Could not find walking saved_model.pb under {base}")


class _SavedModelWalkingExpertSource:
    def __init__(self, *, policy_dir: Path) -> None:
        self.policy_dir = policy_dir

    def rollout(self, *, episodes: int, max_steps: int) -> list[dict[str, Any]]:
        import numpy as np

        env_factory = _require_flybody_walk_env_factory()
        env = env_factory()
        policy = _load_saved_model_policy(self.policy_dir)
        exported: list[dict[str, Any]] = []

        for _ in range(episodes):
            episode_id = _
            timestep = getattr(env, "reset")()
            for step_id in range(max_steps):
                observation = getattr(timestep, "observation")
                mean, std = _infer_distribution(policy, observation)
                exported.append(
                    {
                        "observation": observation,
                        "expert_mean": mean,
                        "expert_log_std": [math.log(max(value, 1e-6)) for value in std],
                        "episode_id": episode_id,
                        "step_id": step_id,
                        "task": "straight_walking",
                    }
                )
                timestep = getattr(env, "step")(np.asarray(mean, dtype=float))
                if _is_terminal_timestep(timestep):
                    break
        return exported


def _require_flybody_walk_env_factory() -> object:
    from flybody.fly_envs import walk_imitation

    return walk_imitation


def _load_saved_model_policy(policy_dir: Path) -> object:
    import tensorflow as tf
    from tensorflow.python.framework import type_spec_registry
    from tensorflow_probability.python.distributions import independent, normal

    _ = independent.Independent(normal.Normal(loc=0.0, scale=1.0), reinterpreted_batch_ndims=0)._type_spec
    legacy_name = "tensorflow_probability.python.distributions.independent.Independent_ACTTypeSpec"
    type_spec_registry._NAME_TO_TYPE_SPEC.setdefault(legacy_name, type(_))
    return tf.saved_model.load(str(policy_dir))


def _infer_distribution(policy: object, observation: Mapping[str, Any]) -> tuple[list[float], list[float]]:
    import tensorflow as tf

    batched = {key: tf.convert_to_tensor(value[None, ...], dtype=tf.float32) for key, value in observation.items()}
    distribution = policy(batched)
    mean_tensor = distribution.mean()[0]
    std_tensor = distribution.stddev()[0]
    return mean_tensor.numpy().astype(float).tolist(), std_tensor.numpy().astype(float).tolist()


def _is_terminal_timestep(timestep: Any) -> bool:
    last = getattr(timestep, "last", None)
    if callable(last):
        return bool(last())
    return False


def _normalize_vector(values: Any) -> list[float]:
    return [float(value) for value in values]
