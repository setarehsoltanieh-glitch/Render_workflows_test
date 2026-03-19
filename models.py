from dataclasses import dataclass, field


@dataclass
class HistoryEntry:
    action_name: str
    params: str
    result: str


@dataclass
class LLMRequest:
    goal: str
    history: list[HistoryEntry]
    available_tools: list[str]


@dataclass
class LLMResponse:
    tool: str        # must match a registered activity name
    params: str      # string argument passed to the tool activity
    is_done: bool = False
    final_answer: str = ""


# --- Planner workflow models ---

@dataclass
class PlanStep:
    tool: str    # activity name to call
    params: str  # argument to pass


@dataclass
class Plan:
    steps: list[PlanStep]
