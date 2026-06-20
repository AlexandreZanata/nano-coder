"""TrainingRun aggregate and state machine (UC-003, STATE-MACHINES.md)."""

from enum import StrEnum


class TrainingRunState(StrEnum):
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


_TERMINAL = frozenset(
    {
        TrainingRunState.FAILED,
        TrainingRunState.CANCELLED,
    }
)

_TRANSITIONS: dict[tuple[TrainingRunState, TrainingRunState], str] = {
    (TrainingRunState.PENDING, TrainingRunState.RUNNING): "start",
    (TrainingRunState.RUNNING, TrainingRunState.COMPLETED): "complete",
    (TrainingRunState.RUNNING, TrainingRunState.FAILED): "fail",
    (TrainingRunState.PENDING, TrainingRunState.FAILED): "fail",
    (TrainingRunState.PENDING, TrainingRunState.CANCELLED): "cancel",
    (TrainingRunState.RUNNING, TrainingRunState.CANCELLED): "cancel",
}


class InvalidTrainingTransition(Exception):
    def __init__(self, current: TrainingRunState, target: TrainingRunState) -> None:
        super().__init__(f"Invalid transition: {current.value} -> {target.value}")


class TrainingRun:
    """Aggregate root for UC-003 smoke and full training runs."""

    def __init__(self, run_id: str, dataset_version: str) -> None:
        self.run_id = run_id
        self.dataset_version = dataset_version
        self.state = TrainingRunState.PENDING

    def transition(self, target: TrainingRunState) -> None:
        if (self.state, target) not in _TRANSITIONS:
            raise InvalidTrainingTransition(self.state, target)
        self.state = target

    @property
    def is_terminal(self) -> bool:
        return self.state in _TERMINAL
