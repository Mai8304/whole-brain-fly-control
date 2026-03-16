from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile a normalized connectome snapshot.")
    parser.add_argument("--snapshot-dir", type=Path, required=True, help="Snapshot directory containing normalized tables")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory for compiled graph artifacts")
    args = parser.parse_args()

    from fruitfly.graph import save_compiled_graph
    from fruitfly.graph.compiler import compile_snapshot
    from fruitfly.snapshot.exporter import load_normalized_snapshot

    nodes, edges = load_normalized_snapshot(args.snapshot_dir)
    compiled = compile_snapshot(nodes=nodes, edges=edges)
    payload = {
        "status": "ok",
        "node_count": len(compiled.node_index),
        "edge_count": len(compiled.edge_index),
        "afferent_count": sum(compiled.afferent_mask),
        "intrinsic_count": sum(compiled.intrinsic_mask),
        "efferent_count": sum(compiled.efferent_mask),
    }
    save_compiled_graph(
        graph=compiled,
        compiled_dir=args.output_dir,
        snapshot_id=args.snapshot_dir.name,
        manifest={"snapshot_dir": str(args.snapshot_dir)},
        config={"source_snapshot_dir": str(args.snapshot_dir)},
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
