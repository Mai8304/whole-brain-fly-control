def test_console_session_tracks_pending_and_applied_state() -> None:
    from fruitfly.evaluation.console_session import ConsoleSession

    session = ConsoleSession.create(
        mode="experiment",
        checkpoint="epoch_0001.pt",
        task="straight_walking",
        environment_physics={"terrain": "flat", "friction": 1.0, "wind": 0.0, "rain": 0.0},
        sensory_inputs={"temperature": 0.0, "odor": 0.0},
    )

    staged = session.stage_changes(
        environment_physics={"terrain": "rough", "friction": 0.8, "wind": 0.3, "rain": 0.1},
        sensory_inputs={"temperature": 0.4, "odor": 0.2},
    )

    assert staged.pending_changes is True
    assert staged.pending_state["environment_physics"]["terrain"] == "rough"
    assert staged.action_provenance["direct_action_editing"] is False
    assert staged.action_provenance["joint_override"] is False

    applied = staged.apply_pending()

    assert applied.pending_changes is False
    assert applied.applied_state["environment_physics"]["terrain"] == "rough"
    assert applied.intervention_log[-1]["changed_fields"] == [
        "environment_physics",
        "sensory_inputs",
    ]
