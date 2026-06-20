"""BenchmarkRun aggregate and state machine (UC-004, STATE-MACHINES.md)."""

from enum import StrEnum


class BenchmarkRunState(StrEnum):
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


_TERMINAL = frozenset(
    {
        BenchmarkRunState.FAILED,
        BenchmarkRunState.CANCELLED,
    }
)

_TRANSITIONS: dict[tuple[BenchmarkRunState, BenchmarkRunState], str] = {
    (BenchmarkRunState.PENDING, BenchmarkRunState.RUNNING): "start",
    (BenchmarkRunState.RUNNING, BenchmarkRunState.COMPLETED): "complete",
    (BenchmarkRunState.RUNNING, BenchmarkRunState.FAILED): "fail",
    (BenchmarkRunState.PENDING, BenchmarkRunState.FAILED): "fail",
    (BenchmarkRunState.PENDING, BenchmarkRunState.CANCELLED): "cancel",
    (BenchmarkRunState.RUNNING, BenchmarkRunState.CANCELLED): "cancel",
}


class InvalidBenchmarkTransition(Exception):
    def __init__(self, current: BenchmarkRunState, target: BenchmarkRunState) -> None:
        super().__init__(f"Invalid transition: {current.value} -> {target.value}")


class BenchmarkRun:
    """Aggregate root for UC-004 benchmark runs."""

    def __init__(self, run_id: str, checkpoint_run_id: str) -> None:
        self.run_id = run_id
        self.checkpoint_run_id = checkpoint_run_id
        self.state = BenchmarkRunState.PENDING

    def transition(self, target: BenchmarkRunState) -> None:
        if (self.state, target) not in _TRANSITIONS:
            raise InvalidBenchmarkTransition(self.state, target)
        self.state = target

    @property
    def is_terminal(self) -> bool:
        return self.state in _TERMINAL
