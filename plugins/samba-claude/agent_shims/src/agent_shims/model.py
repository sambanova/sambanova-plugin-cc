from dataclasses import dataclass, field

@dataclass
class Model:
    context_length: int
    id: str
    max_completion_tokens: int
    sampling_parameters: dict = field(default_factory=dict)
