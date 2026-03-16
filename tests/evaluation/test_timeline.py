def test_build_shared_timeline_payload_exposes_events_and_view_refs() -> None:
    from fruitfly.evaluation.timeline import build_shared_timeline_payload

    payload = build_shared_timeline_payload(
        steps_requested=64,
        steps_completed=12,
        current_step=5,
        events=[
            {"step_id": 2, "event_type": "input_applied", "label": "Input applied"},
            {"step_id": 4, "event_type": "efferent_rise", "label": "Efferent rise"},
        ],
    )

    assert payload["steps_requested"] == 64
    assert payload["steps_completed"] == 12
    assert payload["current_step"] == 5
    assert payload["brain_view_ref"] == "step_id"
    assert payload["body_view_ref"] == "step_id"
    assert payload["events"][0]["event_type"] == "input_applied"
