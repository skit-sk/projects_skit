from viz_lab.provider.opencode_provider import OpenCodeProvider


def create_gemini_flash() -> OpenCodeProvider:
    return OpenCodeProvider(
        name='gemini-2.5-flash',
        model_id='opencode/gemini-3.5-flash',
        provider='google',
        capabilities={'chart', 'code', 'vision'},
        max_tokens=32768,
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
    )


def create_gemini_pro() -> OpenCodeProvider:
    return OpenCodeProvider(
        name='gemini-2.5-pro',
        model_id='opencode/gemini-3.1-pro',
        provider='google',
        capabilities={'chart', 'code', 'vision'},
        max_tokens=65536,
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
    )


def create_free_model() -> OpenCodeProvider:
    return OpenCodeProvider(
        name='deepseek-free',
        model_id='opencode/deepseek-v4-flash-free',
        provider='opencode',
        capabilities={'chart', 'code'},
        max_tokens=8192,
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
    )


providers = [create_free_model, create_gemini_flash, create_gemini_pro]
