from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Process:
    """Immutable description of a process from the input workload."""

    pid: str
    arrival_time: int
    burst_time: int
    priority: int


@dataclass(frozen=True)
class ExecutionSlice:
    """Represents a contiguous CPU run for a specific process."""

    pid: str
    start: int
    end: int

    @property
    def duration(self) -> int:
        return self.end - self.start


@dataclass
class ProcessStats:
    """Per-process metrics derived from execution slices."""

    completion_time: int
    turnaround_time: int
    waiting_time: int
    response_time: int


@dataclass
class AlgorithmResult:
    """Raw output produced by a scheduling algorithm."""

    name: str
    slices: List[ExecutionSlice]
    events: List[str]


@dataclass
class AggregateMetrics:
    """Collection of metrics summarizing a simulation run."""

    per_process: Dict[str, ProcessStats]
    average_turnaround: float
    average_waiting: float
    average_response: float
    context_switches: int


__all__ = [
    "AggregateMetrics",
    "AlgorithmResult",
    "ExecutionSlice",
    "Process",
    "ProcessStats",
]
