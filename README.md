# CPU Scheduling Simulator

**Course:** CENG 301 - Operating Systems

**Student:** Sam Karimpour (ID: 230201911) - Section 1

A Python simulator for six CPU scheduling algorithms. It reads a process workload, prints an ASCII Gantt chart and execution log, calculates per-process metrics, and compares algorithms with optional graphs.

## Requirements

- Python 3.10 or newer (tested with Python 3.13.2).
- Optional: `matplotlib` for comparison graphs.

The simulator and tests use the Python standard library. To enable graph generation:

```bash
python -m pip install -r requirements.txt
```

Without `matplotlib`, all algorithms and text comparisons still run; graph generation is skipped with a message.

## Run

Run these commands from the repository root:

```bash
# Run First Come, First Served
python scheduler/scheduler.py --input processes.txt --algo FCFS

# Run Round Robin with a positive integer quantum
python scheduler/scheduler.py --input processes.txt --algo RR --quantum 4

# Compare all six algorithms and generate graphs
python scheduler/scheduler.py --input processes.txt --algo ALL --quantum 4 --graph-dir graphs

# The module entry point supports the same arguments
python -m scheduler.scheduler --input processes.txt --algo SRTF
```

`--algo` accepts `FCFS`, `SJF`, `SRTF`, `RR`, `PRIO_NP`, `PRIO_P`, or `ALL` (case-insensitive). `RR` requires `--quantum`; `ALL` uses a default quantum of 4 if omitted. Any supplied quantum must be a positive integer.

Each run prints a Gantt chart, chronological execution events, completion/turnaround/waiting/response times, averages, and a context switch count. `ALL` also prints a comparison table and, when `matplotlib` is installed, saves `waiting.png` and `turnaround.png` under `--graph-dir` (default: `graphs`). Generated graphs are excluded from Git.

## Workload format

Each non-comment line contains four whitespace-separated fields:

```text
# pid arrival burst priority
P1 0 7 2
P2 2 4 1
P3 4 9 3
P4 6 5 2
P5 8 2 1
```

- PID is a unique, case-sensitive identifier. `IDLE` is reserved for idle CPU intervals.
- Arrival time is a nonnegative integer; burst time is a positive integer.
- Priority can be any integer; lower values mean higher priority.
- Blank lines and lines beginning with `#` are ignored. At least one process is required.

## Algorithms

| CLI name | Scheduling rule |
| --- | --- |
| `FCFS` | Non-preemptive; select the earliest arrival. |
| `SJF` | Non-preemptive; select the ready process with the shortest burst. |
| `SRTF` | Preemptive; select the ready process with the shortest remaining time. |
| `RR` | Rotate through the ready queue using the specified time quantum. |
| `PRIO_NP` | Non-preemptive; select the ready process with the highest priority. |
| `PRIO_P` | Preemptive; a newly ready process with higher priority can preempt the running process. |

Selection ties are resolved by arrival time, then lexicographic PID. Round Robin preserves ready-queue order: arrivals during a time slice, including at its end, enter the queue before the unfinished running process is requeued.

Turnaround time is completion minus arrival; waiting time is turnaround minus burst; response time is first dispatch minus arrival. Context switches count changes between process IDs, excluding initial dispatch and idle slices. The simulation does not charge time for switching.

## Sample comparison

For the included `processes.txt`, with Round Robin quantum 4:

| Algorithm | Average turnaround | Average waiting | Average response | Context switches |
| --- | ---: | ---: | ---: | ---: |
| FCFS | 14.00 | 8.60 | 8.60 | 4 |
| SJF | 11.20 | 5.80 | 5.80 | 4 |
| SRTF | 10.80 | 5.40 | 4.20 | 6 |
| RR (q=4) | 15.40 | 10.00 | 5.20 | 8 |
| PRIO_NP | 11.20 | 5.80 | 5.80 | 4 |
| PRIO_P | 10.80 | 5.40 | 4.20 | 6 |

For this workload, SRTF and preemptive priority have the lowest average waiting and response times. Round Robin improves response time over FCFS but increases waiting time and context switches. These results depend on the workload and quantum; they do not establish a universally best algorithm.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Project layout

```text
scheduler/
  algorithms/       Scheduling implementations
  utils/            Workload parser, models, metrics, and Gantt helpers
  scheduler.py      CLI and comparison graph generation
tests/              Automated tests
processes.txt       Sample workload
requirements.txt    Optional plotting dependency
```

The original assignment is retained in `CENG 301 Project Fall 2025 (1).pdf`. The duplicate assignment archive and local tool files are excluded from Git. For a course submission, generate the required graphs and record any required execution logs, screenshots, and demo video separately.
