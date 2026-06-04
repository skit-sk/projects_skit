from viz_lab.provider.opencode_provider import OpenCodeProvider


def create_claude_opus() -> OpenCodeProvider:
    return OpenCodeProvider(
        name='claude-4-opus',
        model_id='opencode/claude-opus-4-7',
        provider='anthropic',
        capabilities={'chart', 'code', 'vision'},
        max_tokens=65536,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
    )


def create_claude_sonnet() -> OpenCodeProvider:
    return OpenCodeProvider(
        name='claude-4-sonnet',
        model_id='opencode/claude-sonnet-4-6',
        provider='anthropic',
        capabilities={'chart', 'code'},
        max_tokens=32768,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
    )


providers = [create_claude_opus, create_claude_sonnet]
