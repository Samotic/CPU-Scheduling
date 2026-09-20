from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from .models import AggregateMetrics, ExecutionSlice, Process, ProcessStats


def compute_metrics(processes: List[Process], slices: List[ExecutionSlice]) -> AggregateMetrics:
    """Derive the per-process and aggregate metrics from execution slices."""

    per_process: Dict[str, ProcessStats] = {}
    slice_map: Dict[str, List[ExecutionSlice]] = {p.pid: [] for p in processes}
    for slice_item in slices:
        if slice_item.pid in slice_map:
            slice_map[slice_item.pid].append(slice_item)

    for proc in processes:
        proc_slices = slice_map[proc.pid]
        if not proc_slices:
            raise ValueError(f"Process {proc.pid} never executed; check the algorithm.")
        first_start = min(slice_item.start for slice_item in proc_slices)
        completion_time = max(slice_item.end for slice_item in proc_slices)
        turnaround = completion_time - proc.arrival_time
        waiting = turnaround - proc.burst_time
        response = first_start - proc.arrival_time
        per_process[proc.pid] = ProcessStats(
            completion_time=completion_time,
            turnaround_time=turnaround,
            waiting_time=waiting,
            response_time=response,
        )

    averages = _average_metrics(per_process.values())
    context_switches = count_context_switches(slices)
    return AggregateMetrics(
        per_process=per_process,
        average_turnaround=averages["turnaround"],
        average_waiting=averages["waiting"],
        average_response=averages["response"],
        context_switches=context_switches,
    )


def _average_metrics(stats: Iterable[ProcessStats]) -> Dict[str, float]:
    entries = list(stats)
    total = len(entries)
    if total == 0:
        return {"turnaround": 0.0, "waiting": 0.0, "response": 0.0}
    sum_turnaround = sum(item.turnaround_time for item in entries)
    sum_waiting = sum(item.waiting_time for item in entries)
    sum_response = sum(item.response_time for item in entries)
    return {
        "turnaround": sum_turnaround / total,
        "waiting": sum_waiting / total,
        "response": sum_response / total,
    }


def count_context_switches(slices: List[ExecutionSlice]) -> int:
    """
    Count context switches by examining boundaries between consecutive slices.

    Idle slices are ignored so they don't inflate the switch count.
    """

    previous_pid: str | None = None
    switches = 0
    for slice_item in slices:
        if slice_item.pid == "IDLE":
            continue
        if previous_pid is None:
            previous_pid = slice_item.pid
            continue
        if slice_item.pid != previous_pid:
            switches += 1
            previous_pid = slice_item.pid
    return switches


def format_process_table(processes: List[Process], metrics: AggregateMetrics) -> str:
    """Return a formatted ASCII table that lists per-process statistics."""

    header = (
        f"{'PID':<6}{'Arr':>6}{'Burst':>8}{'Compl':>8}"
        f"{'Turn':>8}{'Wait':>8}{'Resp':>8}"
    )
    lines = [header, "-" * len(header)]
    proc_lookup = {proc.pid: proc for proc in processes}
    for pid, stats in metrics.per_process.items():
        proc = proc_lookup[pid]
        lines.append(
            f"{pid:<6}{proc.arrival_time:>6}{proc.burst_time:>8}"
            f"{stats.completion_time:>8}{stats.turnaround_time:>8}"
            f"{stats.waiting_time:>8}{stats.response_time:>8}"
        )
    lines.append("-" * len(header))
    lines.append(
        f"{'AVG':<6}{'':>6}{'':>8}"
        f"{'':>8}{metrics.average_turnaround:>8.2f}"
        f"{metrics.average_waiting:>8.2f}{metrics.average_response:>8.2f}"
    )
    lines.append(f"Context Switches: {metrics.context_switches}")
    return "\n".join(lines)


def format_comparison_table(rows: List[Tuple[str, AggregateMetrics]]) -> str:
    """Create a summary table comparing multiple algorithms."""

    header = (
        f"{'Algorithm':<12}{'Avg Turn':>12}{'Avg Wait':>12}"
        f"{'Avg Resp':>12}{'Ctx Switches':>15}"
    )
    lines = [header, "-" * len(header)]
    for name, metrics in rows:
        lines.append(
            f"{name:<12}{metrics.average_turnaround:>12.2f}"
            f"{metrics.average_waiting:>12.2f}{metrics.average_response:>12.2f}"
            f"{metrics.context_switches:>15}"
        )
    return "\n".join(lines)


__all__ = [
    "AggregateMetrics",
    "compute_metrics",
    "count_context_switches",
    "format_comparison_table",
    "format_process_table",
]
