from __future__ import annotations

from collections import deque
from typing import List

from ..utils.models import AlgorithmResult, ExecutionSlice, Process
from .common import ProcessState, build_process_states, log_idle_period


def run(processes: List[Process]) -> AlgorithmResult:
    """Simulate the First-Come First-Served scheduling policy."""

    states = build_process_states(processes)
    ready: deque[ProcessState] = deque()
    events: List[str] = []
    slices: List[ExecutionSlice] = []
    time = 0
    next_index = 0
    current: ProcessState | None = None
    current_start = 0
    completed = 0
    total = len(states)

    while completed < total:
        next_index = _enqueue_arrivals(states, next_index, time, ready, events)
        if current is None:
            if ready:
                current = ready.popleft()
                start_phrase = "starts running" if not current.has_started else "resumes running"
                current.has_started = True
                current_start = time
                events.append(f"t={time}: {current.pid} {start_phrase}")
            else:
                if next_index < total:
                    idle_end = states[next_index].arrival_time
                    log_idle_period(slices, events, time, idle_end)
                    time = idle_end
                    continue
                break

        time += 1
        current.remaining_time -= 1
        if current.remaining_time == 0:
            slices.append(ExecutionSlice(pid=current.pid, start=current_start, end=time))
            events.append(f"t={time}: {current.pid} completes")
            current = None
            completed += 1

    return AlgorithmResult(name="FCFS", slices=slices, events=events)


def _enqueue_arrivals(
    states: List[ProcessState],
    next_index: int,
    time: int,
    ready: deque[ProcessState],
    events: List[str],
) -> int:
    """Push all processes whose arrival time has come into the ready queue."""

    total = len(states)
    while next_index < total and states[next_index].arrival_time <= time:
        proc = states[next_index]
        ready.append(proc)
        events.append(f"t={proc.arrival_time}: {proc.pid} arrives")
        next_index += 1
    return next_index


__all__ = ["run"]
