from __future__ import annotations

import heapq
from typing import List

from ..utils.models import AlgorithmResult, ExecutionSlice, Process
from .common import ProcessState, build_process_states, log_idle_period


def run(processes: List[Process]) -> AlgorithmResult:
    """Simulate the non-preemptive Shortest Job First algorithm."""

    states = build_process_states(processes)
    ready: List[tuple[int, int, int, ProcessState]] = []
    events: List[str] = []
    slices: List[ExecutionSlice] = []
    time = 0
    next_index = 0
    completed = 0
    total = len(states)

    while completed < total:
        next_index = _enqueue_available(states, next_index, time, ready, events)
        if not ready:
            if next_index < total:
                idle_end = states[next_index].arrival_time
                log_idle_period(slices, events, time, idle_end)
                time = idle_end
                continue
            break

        _, _, _, current = heapq.heappop(ready)
        start_phrase = "starts running" if not current.has_started else "resumes running"
        current.has_started = True
        events.append(f"t={time}: {current.pid} {start_phrase}")
        start_time = time
        end_time = time + current.remaining_time
        time = end_time
        current.remaining_time = 0
        slices.append(ExecutionSlice(pid=current.pid, start=start_time, end=end_time))
        next_index = _enqueue_available(states, next_index, time, ready, events)
        events.append(f"t={end_time}: {current.pid} completes")
        completed += 1

    return AlgorithmResult(name="SJF", slices=slices, events=events)


def _enqueue_available(
    states: List[ProcessState],
    next_index: int,
    time: int,
    ready: List[tuple[int, int, int, ProcessState]],
    events: List[str],
) -> int:
    """Push all arrived processes into a heap keyed by burst time."""

    total = len(states)
    while next_index < total and states[next_index].arrival_time <= time:
        proc = states[next_index]
        heapq.heappush(
            ready,
            (
                proc.burst_time,
                proc.arrival_time,
                proc.order,
                proc,
            ),
        )
        events.append(f"t={proc.arrival_time}: {proc.pid} arrives")
        next_index += 1
    return next_index


__all__ = ["run"]
