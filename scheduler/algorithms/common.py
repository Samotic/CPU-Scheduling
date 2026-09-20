from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..utils.models import ExecutionSlice, Process


@dataclass
class ProcessState:
    """Mutable runtime representation of a process."""

    pid: str
    arrival_time: int
    burst_time: int
    priority: int
    order: int
    remaining_time: int = field(init=False)
    has_started: bool = field(default=False)

    def __post_init__(self) -> None:
        self.remaining_time = self.burst_time

    @classmethod
    def from_process(cls, process: Process, order: int) -> "ProcessState":
        return cls(
            pid=process.pid,
            arrival_time=process.arrival_time,
            burst_time=process.burst_time,
            priority=process.priority,
            order=order,
        )


def build_process_states(processes: List[Process]) -> List[ProcessState]:
    """Convert immutable Process records into mutable ProcessState objects."""

    ordered = sorted(processes, key=lambda proc: (proc.arrival_time, proc.pid))
    return [ProcessState.from_process(proc, idx) for idx, proc in enumerate(ordered)]


def log_idle_period(
    slices: List[ExecutionSlice],
    events: List[str],
    start: int,
    end: int,
) -> None:
    """Record an idle slice and log the idle interval."""

    if start >= end:
        return
    slices.append(ExecutionSlice(pid="IDLE", start=start, end=end))
    events.append(f"t={start}: CPU idle until t={end}")


__all__ = ["ProcessState", "build_process_states", "log_idle_period"]
