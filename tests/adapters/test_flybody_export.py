def test_export_straight_walking_records_from_injected_source() -> None:
    from fruitfly.adapters.flybody_export import export_straight_walking_records

    class FakeExpertSource:
        def rollout(self, episodes, max_steps):
            assert episodes == 1
            assert max_steps == 10
            return [
                {
                    "observation": {"proprio": [1.0], "command": [0.2]},
                    "command": [0.2],
                    "expert_mean": [0.1, 0.2],
                    "expert_log_std": [-1.0, -1.0],
                    "episode_id": 7,
                    "step_id": 11,
                }
            ]

    records = export_straight_walking_records(
        expert_source=FakeExpertSource(),
        episodes=1,
        max_steps=10,
    )

    assert len(records) == 1
    assert records[0]["observation"] == [1.0, 0.2]
    assert records[0]["command"] == [0.2]
    assert records[0]["expert_mean"] == [0.1, 0.2]
    assert records[0]["episode_id"] == 7
    assert records[0]["step_id"] == 11
    assert records[0]["task"] == "straight_walking"


def test_export_straight_walking_records_normalizes_flybody_observation_without_explicit_command() -> None:
    from fruitfly.adapters.flybody_export import export_straight_walking_records

    class FakeExpertSource:
        def rollout(self, episodes, max_steps):
            assert episodes == 1
            assert max_steps == 2
            return [
                {
                    "observation": {
                        "walker/accelerometer": [1.0, 2.0, 3.0],
                        "walker/ref_displacement": [[0.5, 0.1, 0.0], [0.6, 0.2, 0.0]],
                        "walker/world_zaxis": [0.0, 0.0, 1.0],
                    },
                    "expert_mean": [0.1, 0.2],
                    "expert_log_std": [-1.0, -1.0],
                    "episode_id": 0,
                    "step_id": 1,
                }
            ]

    records = export_straight_walking_records(
        expert_source=FakeExpertSource(),
        episodes=1,
        max_steps=2,
    )

    assert records[0]["observation"] == [1.0, 2.0, 3.0, 0.5, 0.1, 0.0, 0.6, 0.2, 0.0, 0.0, 0.0, 1.0]
    assert records[0]["command"] == [0.5, 0.1]
    assert records[0]["episode_id"] == 0
    assert records[0]["step_id"] == 1
    assert records[0]["task"] == "straight_walking"


def test_export_straight_walking_records_preserves_distinct_episode_and_step_ids() -> None:
    from fruitfly.adapters.flybody_export import export_straight_walking_records

    class FakeExpertSource:
        def rollout(self, episodes, max_steps):
            assert episodes == 2
            assert max_steps == 3
            return [
                {
                    "observation": {"proprio": [1.0], "command": [0.1]},
                    "expert_mean": [0.1],
                    "expert_log_std": [-1.0],
                    "episode_id": 0,
                    "step_id": 0,
                },
                {
                    "observation": {"proprio": [2.0], "command": [0.2]},
                    "expert_mean": [0.2],
                    "expert_log_std": [-1.0],
                    "episode_id": 1,
                    "step_id": 0,
                },
            ]

    records = export_straight_walking_records(
        expert_source=FakeExpertSource(),
        episodes=2,
        max_steps=3,
    )

    assert [record["episode_id"] for record in records] == [0, 1]
    assert [record["step_id"] for record in records] == [0, 0]


def test_resolve_walking_policy_dir_accepts_download_root(tmp_path) -> None:
    from fruitfly.adapters.flybody_export import _resolve_walking_policy_dir

    walking_dir = tmp_path / "walking"
    walking_dir.mkdir()
    (walking_dir / "saved_model.pb").write_text("stub", encoding="utf-8")

    assert _resolve_walking_policy_dir(tmp_path) == walking_dir
