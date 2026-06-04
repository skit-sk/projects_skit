from viz_lab.provider.opencode_provider import OpenCodeProvider


def create_gpt4o() -> OpenCodeProvider:
    return OpenCodeProvider(
        name='gpt-4o',
        model_id='opencode/gpt-5.4-pro',
        provider='openai',
        capabilities={'chart', 'code', 'image'},
        max_tokens=32768,
        cost_per_1k_input=0.0025,
        cost_per_1k_output=0.01,
    )


def create_gpt4o_mini() -> OpenCodeProvider:
    return OpenCodeProvider(
        name='gpt-4o-mini',
        model_id='opencode/gpt-5.4-mini',
        provider='openai',
        capabilities={'chart', 'code'},
        max_tokens=16384,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
    )


providers = [create_gpt4o, create_gpt4o_mini]
