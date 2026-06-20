from enum import StrEnum


class DatasetGenerationState(StrEnum):
    PENDING = "Pending"
    GENERATING = "Generating"
    FILTERING = "Filtering"
    AWAITING_MANUAL_REVIEW = "AwaitingManualReview"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


_TERMINAL = frozenset(
    {
        DatasetGenerationState.FAILED,
        DatasetGenerationState.CANCELLED,
    }
)

_TRANSITIONS: dict[tuple[DatasetGenerationState, DatasetGenerationState], str] = {
    (DatasetGenerationState.PENDING, DatasetGenerationState.GENERATING): "start",
    (DatasetGenerationState.GENERATING, DatasetGenerationState.FILTERING): "generationComplete",
    (DatasetGenerationState.GENERATING, DatasetGenerationState.FAILED): "generationFailed",
    (DatasetGenerationState.FILTERING, DatasetGenerationState.AWAITING_MANUAL_REVIEW): "awaitReview",
    (DatasetGenerationState.FILTERING, DatasetGenerationState.COMPLETED): "filterComplete",
    (DatasetGenerationState.AWAITING_MANUAL_REVIEW, DatasetGenerationState.COMPLETED): "approve",
    (DatasetGenerationState.AWAITING_MANUAL_REVIEW, DatasetGenerationState.FAILED): "reject",
}


class InvalidStateTransition(Exception):
    def __init__(self, current: DatasetGenerationState, target: DatasetGenerationState) -> None:
        super().__init__(f"Invalid transition: {current.value} -> {target.value}")


class DatasetGenerationRun:
    """Aggregate root for UC-001 — Stage 4 generation phase."""

    def __init__(self, run_id: str, target_language: str) -> None:
        self.run_id = run_id
        self.target_language = target_language
        self.state = DatasetGenerationState.PENDING

    def transition(self, target: DatasetGenerationState) -> None:
        if (self.state, target) not in _TRANSITIONS:
            raise InvalidStateTransition(self.state, target)
        self.state = target

    @property
    def is_terminal(self) -> bool:
        return self.state in _TERMINAL
