from __future__ import annotations

from collections import deque
from typing import Deque, List

from ..utils.models import AlgorithmResult, ExecutionSlice, Process
from .common import ProcessState, build_process_states, log_idle_period


def run(processes: List[Process], quantum: int) -> AlgorithmResult:
    """Simulate Round Robin scheduling with the provided time quantum."""

    if quantum <= 0:
        raise ValueError("Time quantum must be a positive integer.")

    states = build_process_states(processes)
    ready: Deque[ProcessState] = deque()
    events: List[str] = []
    slices: List[ExecutionSlice] = []
    time = 0
    next_index = 0
    completed = 0
    total = len(states)

    while completed < total:
        next_index = _enqueue_arrivals(states, next_index, time, ready, events)
        if not ready:
            if next_index < total:
                idle_end = states[next_index].arrival_time
                log_idle_period(slices, events, time, idle_end)
                time = idle_end
                continue
            break

        current = ready.popleft()
        start_phrase = "starts running" if not current.has_started else "resumes running"
        current.has_started = True
        events.append(f"t={time}: {current.pid} {start_phrase}")
        run_time = min(quantum, current.remaining_time)
        start_time = time
        time += run_time
        current.remaining_time -= run_time
        slices.append(ExecutionSlice(pid=current.pid, start=start_time, end=time))
        next_index = _enqueue_arrivals(states, next_index, time, ready, events)

        if current.remaining_time == 0:
            events.append(f"t={time}: {current.pid} completes")
            completed += 1
        else:
            events.append(f"t={time}: {current.pid} quantum expired")
            ready.append(current)

    return AlgorithmResult(name=f"RR(q={quantum})", slices=slices, events=events)


def _enqueue_arrivals(
    states: List[ProcessState],
    next_index: int,
    time: int,
    ready: Deque[ProcessState],
    events: List[str],
) -> int:
    total = len(states)
    while next_index < total and states[next_index].arrival_time <= time:
        proc = states[next_index]
        ready.append(proc)
        events.append(f"t={proc.arrival_time}: {proc.pid} arrives")
        next_index += 1
    return next_index


__all__ = ["run"]
