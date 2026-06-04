from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FileRef:
    path: str
    name: str
    mime: str = 'text/plain'
    size_bytes: int = 0


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    duration_ms: float = 0.0
    cost_usd: float = 0.0


@dataclass
class ProviderResponse:
    text: str = ''
    files: list[FileRef] = field(default_factory=list)
    script: Optional[str] = None
    usage: TokenUsage = field(default_factory=TokenUsage)


class ModelProvider(ABC):
    name: str = ''
    provider: str = ''
    capabilities: set[str] = set()
    max_tokens: int = 4096
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0

    @abstractmethod
    def generate(self, prompt: str, context: list[FileRef] | None = None) -> ProviderResponse:
        pass

    @abstractmethod
    def render(self, data: dict, chart_type: str) -> ProviderResponse:
        pass

    def to_dict(self) -> dict:
        return {
            'id': self.name,
            'name': self.name.replace('-', ' ').title(),
            'provider': self.provider,
            'capabilities': list(self.capabilities),
            'max_tokens': self.max_tokens,
            'cost_per_1k_input': self.cost_per_1k_input,
            'cost_per_1k_output': self.cost_per_1k_output,
        }
