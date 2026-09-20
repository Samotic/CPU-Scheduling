from __future__ import annotations

from pathlib import Path
from typing import List

from .models import Process


def load_processes(path: str | Path) -> List[Process]:
    """
    Read a workload description file and return a list of Process objects.

    The accepted format follows the specification:
    # comment lines are ignored
    pid arrival_time burst_time priority
    """

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    processes: List[Process] = []
    seen_pids: set[str] = set()
    with file_path.open(encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            tokens = line.split()
            if len(tokens) != 4:
                raise ValueError(
                    f"Line {line_no} must contain pid, arrival, burst, priority"
                )
            pid, arrival, burst, priority = tokens
            try:
                arrival_time = int(arrival)
                burst_time = int(burst)
                priority_value = int(priority)
            except ValueError as exc:
                raise ValueError(
                    f"Line {line_no} contains a non-integer field: {raw_line.strip()}"
                ) from exc
            if pid == "IDLE":
                raise ValueError(f"Line {line_no}: PID 'IDLE' is reserved for idle intervals.")
            if pid in seen_pids:
                raise ValueError(f"Line {line_no}: duplicate PID '{pid}'.")
            if arrival_time < 0:
                raise ValueError(f"Line {line_no}: arrival time must be non-negative.")
            if burst_time <= 0:
                raise ValueError(f"Line {line_no}: burst time must be positive.")
            seen_pids.add(pid)
            processes.append(
                Process(
                    pid=pid,
                    arrival_time=arrival_time,
                    burst_time=burst_time,
                    priority=priority_value,
                )
            )

    if not processes:
        raise ValueError("No processes were found in the input file.")

    return processes


__all__ = ["load_processes"]
