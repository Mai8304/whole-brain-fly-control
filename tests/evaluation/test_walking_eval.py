def test_eval_marks_direction_change_for_turning_rollout() -> None:
    from fruitfly.evaluation.walking_eval import summarize_turning

    summary = summarize_turning(headings=[0.0, 0.1, 0.3, 0.6])
    assert summary["direction_changed"] is True
