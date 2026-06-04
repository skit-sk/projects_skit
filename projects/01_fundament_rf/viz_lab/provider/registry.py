import json
import os
from typing import Optional
from viz_lab.provider.base import ModelProvider


class ProviderRegistry:
    def __init__(self):
        self._providers: dict[str, ModelProvider] = {}

    def register(self, provider: ModelProvider):
        self._providers[provider.name] = provider

    def get(self, name: str) -> Optional[ModelProvider]:
        return self._providers.get(name)

    def list_all(self) -> list[dict]:
        return [p.to_dict() for p in self._providers.values()]

    def list_by_capability(self, cap: str) -> list[ModelProvider]:
        return [p for p in self._providers.values() if cap in p.capabilities]

    def load_custom(self, config_path: str):
        if not os.path.exists(config_path):
            return
        with open(config_path) as f:
            configs = json.load(f)
        for cfg in configs:
            provider = CustomProvider(cfg)
            self.register(provider)

    def init_defaults(self):
        from viz_lab.provider.gemini import providers as gemini_providers
        from viz_lab.provider.openai import providers as openai_providers
        from viz_lab.provider.anthropic import providers as anthropic_providers
        from viz_lab.provider.tradingview import providers as tv_providers
        from viz_lab.provider.voice import providers as voice_providers

        all_factories = (gemini_providers + openai_providers + anthropic_providers
                         + tv_providers + voice_providers)
        for factory in all_factories:
            provider = factory()
            self.register(provider)

    def to_dict(self) -> dict:
        return {
            'providers': self.list_all(),
            'count': len(self._providers),
        }


class CustomProvider(ModelProvider):
    def __init__(self, config: dict):
        self.name = config.get('id', 'custom')
        self.provider = config.get('type', 'custom')
        self.capabilities = set(config.get('capabilities', []))
        self.endpoint = config.get('endpoint', '')
        self.auth = config.get('auth', '')
        self.model = config.get('model', '')

    def generate(self, prompt: str, context=None):
        from viz_lab.provider.opencode_provider import OpenCodeProvider
        provider = OpenCodeProvider(
            name=self.name,
            model_id=self.model or self.name,
            provider=self.provider,
            capabilities=self.capabilities,
        )
        return provider.generate(prompt, context)

    def render(self, data: dict, chart_type: str):
        from viz_lab.provider.opencode_provider import OpenCodeProvider
        provider = OpenCodeProvider(
            name=self.name,
            model_id=self.model or self.name,
            provider=self.provider,
            capabilities=self.capabilities,
        )
        return provider.render(data, chart_type)


_registry = ProviderRegistry()


def get_registry() -> ProviderRegistry:
    return _registry
