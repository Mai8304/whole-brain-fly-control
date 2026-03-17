from __future__ import annotations

from importlib import import_module
from typing import Any

from .brain_asset_manifest import build_default_neuropil_manifest, load_brain_asset_manifest
from .inspector_trace import ReplayTracePayload, dump_replay_trace, load_replay_trace
from .neuropil_manifest import build_v1_neuropil_manifest
from .neural_activity import summarize_neural_activity
from .replay_renderer import RenderedReplayFrame, ReplayRenderer
from .walking_eval import summarize_closed_loop_rollout, summarize_gait_initiation, summarize_straight_walking, summarize_turning

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {}

__all__ = [
    "build_default_neuropil_manifest",
    "build_v1_neuropil_manifest",
    "load_brain_asset_manifest",
    "load_replay_trace",
    "dump_replay_trace",
    "ReplayTracePayload",
    "RenderedReplayFrame",
    "ReplayRenderer",
    "summarize_neural_activity",
    "summarize_closed_loop_rollout",
    "summarize_gait_initiation",
    "summarize_straight_walking",
    "summarize_turning",
]


def __getattr__(name: str) -> Any:
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = _LAZY_EXPORTS[name]
    module = import_module(module_name, package=__name__)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
