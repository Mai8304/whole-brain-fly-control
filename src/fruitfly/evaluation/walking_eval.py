from __future__ import annotations

import math
from collections.abc import Sequence


def summarize_gait_initiation(contact_events: Sequence[float]) -> dict[str, bool]:
    return {"started": bool(contact_events)}


def summarize_straight_walking(steps_without_collapse: int) -> dict[str, bool | int]:
    return {
        "stable": steps_without_collapse >= 100,
        "steps_without_collapse": steps_without_collapse,
    }


def summarize_turning(headings: Sequence[float]) -> dict[str, bool | float]:
    if len(headings) < 2:
        delta = 0.0
    else:
        delta = float(headings[-1] - headings[0])
    return {
        "heading_delta": delta,
        "direction_changed": abs(delta) > 0.2,
    }


def summarize_closed_loop_rollout(
    *,
    task: str,
    checkpoint: str,
    steps_requested: int,
    steps_completed: int,
    terminated_early: bool,
    actions: Sequence[Sequence[float]],
    rewards: Sequence[float],
    heading_trace: Sequence[float],
    forward_velocity_trace: Sequence[float],
    upright_trace: Sequence[float],
    error: str | None = None,
) -> dict[str, bool | float | int | str]:
    has_nan_action = any(not math.isfinite(float(value)) for action in actions for value in action)
    action_norms = [math.sqrt(sum(float(value) * float(value) for value in action)) for action in actions]
    mean_action_norm = float(sum(action_norms) / len(action_norms)) if action_norms else 0.0
    reward_mean = float(sum(float(reward) for reward in rewards) / len(rewards)) if rewards else 0.0
    final_reward = float(rewards[-1]) if rewards else 0.0
    if len(heading_trace) >= 2:
        final_heading_delta = float(heading_trace[-1] - heading_trace[0])
    else:
        final_heading_delta = 0.0
    forward_velocity_mean = (
        float(sum(float(value) for value in forward_velocity_trace) / len(forward_velocity_trace))
        if forward_velocity_trace
        else 0.0
    )
    if forward_velocity_trace:
        variance = sum(
            (float(value) - forward_velocity_mean) * (float(value) - forward_velocity_mean)
            for value in forward_velocity_trace
        ) / len(forward_velocity_trace)
        forward_velocity_std = float(math.sqrt(variance))
    else:
        forward_velocity_std = 0.0
    body_upright_mean = (
        float(sum(float(value) for value in upright_trace) / len(upright_trace))
        if upright_trace
        else 0.0
    )

    summary: dict[str, bool | float | int | str] = {
        "status": "failed" if error or has_nan_action else "ok",
        "task": task,
        "checkpoint": checkpoint,
        "steps_requested": int(steps_requested),
        "steps_completed": int(steps_completed),
        "terminated_early": bool(terminated_early),
        "has_nan_action": bool(has_nan_action),
        "mean_action_norm": mean_action_norm,
        "reward_mean": reward_mean,
        "final_reward": final_reward,
        "final_heading_delta": final_heading_delta,
        "forward_velocity_mean": forward_velocity_mean,
        "forward_velocity_std": forward_velocity_std,
        "body_upright_mean": body_upright_mean,
    }
    if error is not None:
        summary["error"] = error
    return summary
