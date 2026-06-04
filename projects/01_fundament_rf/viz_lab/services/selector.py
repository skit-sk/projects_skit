from viz_lab.provider.registry import get_registry
from viz_lab.provider.base import ModelProvider


class SelectorRule:
    def __init__(self, data_type: str = '', complexity: str = '',
                 has_indicators: bool | None = None,
                 has_images: bool | None = None,
                 models: list[str] | None = None,
                 priority: int = 0):
        self.data_type = data_type
        self.complexity = complexity
        self.has_indicators = has_indicators
        self.has_images = has_images
        self.models = models or []
        self.priority = priority


class ModelSelector:
    def __init__(self):
        self.rules: list[SelectorRule] = [
            SelectorRule(data_type='ohlcv', complexity='simple',
                         models=['tv-screenshot', 'gemini-2.5-flash'],
                         priority=10),
            SelectorRule(data_type='ohlcv', complexity='medium',
                         has_indicators=True,
                         models=['gemini-2.5-flash', 'deepseek-free', 'gpt-4o-mini'],
                         priority=9),
            SelectorRule(data_type='timeseries', complexity='simple',
                         models=['deepseek-free', 'gemini-2.5-flash'],
                         priority=8),
            SelectorRule(data_type='timeseries', complexity='complex',
                         has_indicators=True,
                         models=['gemini-2.5-flash', 'gpt-4o-mini', 'claude-4-sonnet'],
                         priority=7),
            SelectorRule(data_type='categorical', complexity='simple',
                         models=['deepseek-free'],
                         priority=6),
            SelectorRule(data_type='image', complexity='simple',
                         models=['gemini-2.5-flash', 'claude-4-opus'],
                         priority=5),
            SelectorRule(data_type='comparison', complexity='medium',
                         models=['gemini-2.5-flash', 'gpt-4o-mini'],
                         priority=9),
            SelectorRule(data_type='tabular', complexity='simple',
                         models=['deepseek-free'],
                         priority=4),
            SelectorRule(data_type='unknown', complexity='simple',
                         models=['deepseek-free'],
                         priority=1),
        ]

    def suggest(self, classification: dict, profile: dict, intent: dict) -> list[dict]:
        data_type = classification.get('primary_type', 'unknown')
        complexity = classification.get('complexity', 'simple')
        has_indicators = len(intent.get('indicators', [])) > 0
        has_images = profile.get('data_type') == 'image'

        matched = []
        for rule in self.rules:
            score = 0
            if rule.data_type and rule.data_type == data_type:
                score += rule.priority * 10
            if rule.complexity and rule.complexity == complexity:
                score += rule.priority * 5
            if rule.has_indicators is not None and rule.has_indicators == has_indicators:
                score += rule.priority * 3
            if rule.has_images is not None and rule.has_images == has_images:
                score += rule.priority * 3

            if score > 0:
                for model_name in rule.models:
                    matched.append({
                        'model': model_name,
                        'score': score,
                        'reason': f'{rule.data_type}/{rule.complexity} match',
                    })

        matched.sort(key=lambda x: x['score'], reverse=True)

        seen = set()
        unique = []
        for m in matched:
            if m['model'] not in seen:
                seen.add(m['model'])
                unique.append(m)

        registry = get_registry()
        enriched = []
        for m in unique[:5]:
            provider = registry.get(m['model'])
            if provider:
                d = provider.to_dict()
                d['score'] = m['score']
                d['reason'] = m['reason']
                enriched.append(d)
            else:
                enriched.append({
                    'id': m['model'],
                    'name': m['model'],
                    'provider': 'unknown',
                    'capabilities': [],
                    'score': m['score'],
                    'reason': m['reason'],
                })

        return enriched

    def select(self, classification: dict, profile: dict, intent: dict,
               preferred_models: list[str] | None = None) -> list[str]:
        suggestions = self.suggest(classification, profile, intent)
        if preferred_models:
            ordered = [m for m in preferred_models if any(s['id'] == m for s in suggestions)]
            remaining = [s['id'] for s in suggestions if s['id'] not in ordered]
            return ordered + remaining
        return [s['id'] for s in suggestions]


selector = ModelSelector()


def get_selector() -> ModelSelector:
    return selector
