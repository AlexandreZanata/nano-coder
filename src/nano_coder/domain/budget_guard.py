from dataclasses import dataclass


@dataclass(frozen=True)
class TokenPricing:
    input_usd_per_million: float
    output_usd_per_million: float

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        input_cost = input_tokens * self.input_usd_per_million / 1_000_000
        output_cost = output_tokens * self.output_usd_per_million / 1_000_000
        return input_cost + output_cost


class BudgetExceeded(Exception):
    """BR-006 — cumulative TeacherModel API cost exceeded maxBudgetUsd."""

    def __init__(self, spent_usd: float, max_budget_usd: float) -> None:
        self.spent_usd = spent_usd
        self.max_budget_usd = max_budget_usd
        super().__init__(
            f"BudgetExceeded: spent ${spent_usd:.4f} exceeds max ${max_budget_usd:.2f}"
        )


class SeedCountInsufficient(Exception):
    """BR-001 — not enough gold seeds to start expansion."""

    def __init__(self, language: str, count: int, minimum: int) -> None:
        self.language = language
        self.count = count
        self.minimum = minimum
        super().__init__(
            f"SeedCountInsufficient: {language} has {count} seeds, need >= {minimum}"
        )


@dataclass
class BudgetGuard:
    max_budget_usd: float
    pricing: TokenPricing
    spent_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0

    def record(self, input_tokens: int, output_tokens: int) -> float:
        cost = self.pricing.estimate_cost(input_tokens, output_tokens)
        self.spent_usd += cost
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        if self.spent_usd > self.max_budget_usd:
            raise BudgetExceeded(self.spent_usd, self.max_budget_usd)
        return cost
