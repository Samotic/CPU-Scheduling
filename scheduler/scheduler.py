from __future__ import annotations

import argparse
import os
from typing import Callable, Dict, List, Sequence, Tuple

if __package__:
    from .algorithms import fcfs, priority_np, priority_p, rr, sjf, srtf
    from .utils import gantt, parser, statistics
    from .utils.models import AggregateMetrics, AlgorithmResult
else:  # Support running via `python scheduler/scheduler.py`
    import sys
    from pathlib import Path

    PACKAGE_ROOT = Path(__file__).resolve().parent.parent
    if str(PACKAGE_ROOT) not in sys.path:
        sys.path.insert(0, str(PACKAGE_ROOT))
    from scheduler.algorithms import fcfs, priority_np, priority_p, rr, sjf, srtf
    from scheduler.utils import gantt, parser, statistics
    from scheduler.utils.models import AggregateMetrics, AlgorithmResult


AlgorithmRunner = Callable[..., AlgorithmResult]


def parse_args() -> argparse.Namespace:
    parser_obj = argparse.ArgumentParser(
        description="CPU Scheduling Simulator for CENG 301 Project",
    )
    parser_obj.add_argument(
        "--input",
        required=True,
        help="Path to the process description text file.",
    )
    parser_obj.add_argument(
        "--algo",
        required=True,
        type=lambda value: value.strip().upper(),
        choices=["FCFS", "SJF", "SRTF", "RR", "PRIO_NP", "PRIO_P", "ALL"],
        help="Algorithm to run (FCFS, SJF, SRTF, RR, PRIO_NP, PRIO_P, or ALL).",
    )
    parser_obj.add_argument(
        "--quantum",
        type=int,
        help="Time quantum (required for RR, used when ALL includes RR).",
    )
    parser_obj.add_argument(
        "--graph-dir",
        default="graphs",
        help="Directory where matplotlib graphs will be stored.",
    )
    args = parser_obj.parse_args()
    if args.quantum is not None and args.quantum <= 0:
        parser_obj.error("--quantum must be a positive integer.")
    if args.algo == "RR" and args.quantum is None:
        parser_obj.error("--quantum is required when running RR directly.")
    try:
        args.processes = parser.load_processes(args.input)
    except (OSError, ValueError) as exc:
        parser_obj.error(str(exc))
    return args


def main() -> None:
    args = parse_args()
    processes = args.processes
    algo_keys = resolve_algorithms(args.algo)
    quantum = args.quantum if args.quantum is not None else 4

    algorithm_map: Dict[str, AlgorithmRunner] = {
        "FCFS": lambda procs: fcfs.run(procs),
        "SJF": lambda procs: sjf.run(procs),
        "SRTF": lambda procs: srtf.run(procs),
        "RR": lambda procs: rr.run(procs, quantum=quantum),
        "PRIO_NP": lambda procs: priority_np.run(procs),
        "PRIO_P": lambda procs: priority_p.run(procs),
    }

    collected: List[Tuple[str, AlgorithmResult, AggregateMetrics]] = []

    for key in algo_keys:
        runner = algorithm_map[key]
        result = runner(processes)
        metrics = statistics.compute_metrics(processes, result.slices)
        collected.append((key, result, metrics))
        print("=" * 80)
        print(f"Algorithm: {result.name}")
        print("-" * 80)
        print("ASCII Gantt Chart")
        print(gantt.build_gantt_chart(result.slices))
        print("\nExecution Log:")
        for entry in result.events:
            print(f"  {entry}")
        print("\nPer-Process Metrics:")
        print(statistics.format_process_table(processes, metrics))

    if len(collected) > 1:
        summary_rows = [(result.name, metrics) for _, result, metrics in collected]
        print("\nComparison Summary:")
        print(statistics.format_comparison_table(summary_rows))
        save_graphs(summary_rows, args.graph_dir)


def resolve_algorithms(selection: str) -> List[str]:
    ordered = ["FCFS", "SJF", "SRTF", "RR", "PRIO_NP", "PRIO_P"]
    available = set(ordered)
    choice = selection.strip().upper()
    if choice == "ALL":
        return ordered
    if choice not in available:
        raise ValueError(f"Unknown algorithm selection: {selection}")
    return [choice]


def save_graphs(
    summaries: Sequence[Tuple[str, AggregateMetrics]],
    graph_dir: str,
) -> None:
    """Persist matplotlib bar charts for average waiting and turnaround times."""

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib is not installed; skipping graph generation.")
        return

    os.makedirs(graph_dir, exist_ok=True)
    algorithms = [name for name, _ in summaries]
    avg_waiting = [metrics.average_waiting for _, metrics in summaries]
    avg_turnaround = [metrics.average_turnaround for _, metrics in summaries]

    plt.figure(figsize=(8, 4))
    plt.bar(algorithms, avg_waiting, color="#4e79a7")
    plt.xlabel("Algorithm")
    plt.ylabel("Average Waiting Time")
    plt.title("Average Waiting Time vs Algorithm")
    plt.tight_layout()
    plt.savefig(os.path.join(graph_dir, "waiting.png"))
    plt.close()

    plt.figure(figsize=(8, 4))
    plt.bar(algorithms, avg_turnaround, color="#f28e2c")
    plt.xlabel("Algorithm")
    plt.ylabel("Average Turnaround Time")
    plt.title("Average Turnaround Time vs Algorithm")
    plt.tight_layout()
    plt.savefig(os.path.join(graph_dir, "turnaround.png"))
    plt.close()

    print(f"Graphs saved under: {os.path.abspath(graph_dir)}")


if __name__ == "__main__":
    main()
