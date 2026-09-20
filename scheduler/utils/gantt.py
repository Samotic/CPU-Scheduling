from __future__ import annotations

from typing import List

from .models import ExecutionSlice


def build_gantt_chart(slices: List[ExecutionSlice]) -> str:
    """Create an ASCII Gantt chart from the provided execution slices."""

    if not slices:
        return "No execution slices recorded."

    chart_segments = []
    for slice_item in slices:
        width = max(2, slice_item.duration * 2)
        label = slice_item.pid
        chart_segments.append(f"|{label.center(width, '-')}")
    chart_segments.append("|")
    chart_line = "".join(chart_segments)

    last_time = max(slice_item.end for slice_item in slices)
    time_line = "Time : " + " ".join(str(t) for t in range(0, last_time + 1))

    boundaries = [slices[0].start]
    for slice_item in slices:
        boundaries.append(slice_item.end)
    boundaries_line = "Boundaries: " + " -> ".join(str(bound) for bound in boundaries)

    return "\n".join([time_line, chart_line, boundaries_line])


__all__ = ["build_gantt_chart"]
