def test_summarize_closed_loop_rollout_exposes_required_fields() -> None:
    from fruitfly.evaluation.walking_eval import summarize_closed_loop_rollout

    summary = summarize_closed_loop_rollout(
        task="straight_walking",
        checkpoint="checkpoint.pt",
        steps_requested=8,
        steps_completed=5,
        terminated_early=True,
        actions=[[0.1, 0.2], [0.2, 0.3]],
        rewards=[0.5, 0.7],
        heading_trace=[0.0, 0.1],
        forward_velocity_trace=[0.2, 0.4],
        upright_trace=[1.0, 0.8],
    )

    assert summary["status"] == "ok"
    assert summary["task"] == "straight_walking"
    assert summary["checkpoint"] == "checkpoint.pt"
    assert summary["steps_requested"] == 8
    assert summary["steps_completed"] == 5
    assert summary["terminated_early"] is True
    assert summary["has_nan_action"] is False
    assert "mean_action_norm" in summary
    assert summary["final_reward"] == 0.7
    assert summary["final_heading_delta"] == 0.1
    assert summary["reward_mean"] == 0.6
    assert summary["forward_velocity_mean"] == 0.30000000000000004
    assert summary["forward_velocity_std"] == 0.1
    assert summary["body_upright_mean"] == 0.9
