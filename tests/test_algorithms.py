import unittest

from scheduler.algorithms import fcfs, priority_np, priority_p, rr, sjf, srtf
from scheduler.utils.models import Process
from scheduler.utils.statistics import compute_metrics


RUNNERS = {
    "FCFS": fcfs.run,
    "SJF": sjf.run,
    "SRTF": srtf.run,
    "RR": lambda processes: rr.run(processes, quantum=2),
    "PRIO_NP": priority_np.run,
    "PRIO_P": priority_p.run,
}


def schedule(result):
    return [(item.pid, item.start, item.end) for item in result.slices]


class AlgorithmTests(unittest.TestCase):
    def test_known_schedules(self):
        processes = [
            Process("A", 0, 5, 2),
            Process("B", 1, 2, 1),
            Process("C", 2, 1, 3),
        ]
        expected = {
            "FCFS": [("A", 0, 5), ("B", 5, 7), ("C", 7, 8)],
            "SJF": [("A", 0, 5), ("C", 5, 6), ("B", 6, 8)],
            "SRTF": [("A", 0, 1), ("B", 1, 3), ("C", 3, 4), ("A", 4, 8)],
            "RR": [("A", 0, 2), ("B", 2, 4), ("C", 4, 5), ("A", 5, 7), ("A", 7, 8)],
            "PRIO_NP": [("A", 0, 5), ("B", 5, 7), ("C", 7, 8)],
            "PRIO_P": [("A", 0, 1), ("B", 1, 3), ("A", 3, 7), ("C", 7, 8)],
        }
        for name, runner in RUNNERS.items():
            with self.subTest(algorithm=name):
                self.assertEqual(schedule(runner(processes)), expected[name])

    def test_preempted_process_metrics(self):
        processes = [
            Process("A", 0, 5, 2),
            Process("B", 1, 2, 1),
            Process("C", 2, 1, 3),
        ]
        result = srtf.run(processes)
        metrics = compute_metrics(processes, result.slices)
        expected = {"A": (8, 8, 3, 0), "B": (3, 2, 0, 0), "C": (4, 2, 1, 1)}
        for pid, values in expected.items():
            with self.subTest(pid=pid):
                stats = metrics.per_process[pid]
                self.assertEqual(
                    (stats.completion_time, stats.turnaround_time, stats.waiting_time, stats.response_time),
                    values,
                )
        self.assertAlmostEqual(metrics.average_turnaround, 4)
        self.assertAlmostEqual(metrics.average_waiting, 4 / 3)
        self.assertAlmostEqual(metrics.average_response, 1 / 3)
        self.assertEqual(metrics.context_switches, 3)

    def test_initial_and_intermediate_idle_periods(self):
        processes = [Process("A", 3, 2, 2), Process("B", 8, 1, 1)]
        expected = [("IDLE", 0, 3), ("A", 3, 5), ("IDLE", 5, 8), ("B", 8, 9)]
        for name, runner in RUNNERS.items():
            with self.subTest(algorithm=name):
                result = runner(processes)
                self.assertEqual(schedule(result), expected)
                metrics = compute_metrics(processes, result.slices)
                self.assertEqual(metrics.average_waiting, 0)
                self.assertEqual(metrics.average_response, 0)
                self.assertEqual(metrics.context_switches, 1)

    def test_arrivals_are_logged_in_chronological_order(self):
        processes = [Process("A", 0, 5, 2), Process("B", 1, 1, 1), Process("C", 3, 1, 3)]
        for name, runner in RUNNERS.items():
            with self.subTest(algorithm=name):
                events = runner(processes).events
                times = [int(event.split(":", 1)[0][2:]) for event in events]
                self.assertEqual(times, sorted(times))
                for process in processes:
                    self.assertEqual(events.count(f"t={process.arrival_time}: {process.pid} arrives"), 1)

    def test_equal_priority_does_not_preempt_current_process(self):
        processes = [Process("A", 0, 5, 2), Process("B", 1, 2, 2)]
        result = priority_p.run(processes)
        self.assertEqual(schedule(result), [("A", 0, 5), ("B", 5, 7)])
        self.assertFalse(any("preempted" in event for event in result.events))

    def test_equal_remaining_time_does_not_preempt_current_process(self):
        processes = [Process("A", 0, 3, 2), Process("B", 1, 2, 1)]
        result = srtf.run(processes)
        self.assertEqual(schedule(result), [("A", 0, 3), ("B", 3, 5)])
        self.assertFalse(any("preempted" in event for event in result.events))

    def test_round_robin_enqueues_boundary_arrival_before_expired_process(self):
        processes = [Process("A", 0, 4, 1), Process("B", 2, 1, 1)]
        self.assertEqual(schedule(rr.run(processes, quantum=2)), [("A", 0, 2), ("B", 2, 3), ("A", 3, 5)])

    def test_consecutive_round_robin_slices_do_not_count_as_context_switches(self):
        processes = [Process("A", 0, 5, 1)]
        metrics = compute_metrics(processes, rr.run(processes, quantum=2).slices)
        self.assertEqual(metrics.context_switches, 0)
        self.assertEqual(metrics.average_waiting, 0)

    def test_simultaneous_arrivals_use_pid_tiebreaker(self):
        processes = [Process("B", 0, 1, 1), Process("A", 0, 1, 1)]
        for name, runner in RUNNERS.items():
            with self.subTest(algorithm=name):
                self.assertEqual(schedule(runner(processes)), [("A", 0, 1), ("B", 1, 2)])


if __name__ == "__main__":
    unittest.main()
