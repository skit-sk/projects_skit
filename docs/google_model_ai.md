# Google AI (Gemini API) — модель для транскрипции

**Источник:** https://ai.google.dev  
**API:** https://generativelanguage.googleapis.com/v1  
**Ключ:** `GEMINI_API_KEY` (получить в [aistudio.google.com](https://aistudio.google.com))

---

## Доступные модели

### Gemini 3 (текущее поколение)

| Модель | Статус | Контекст | Цена Input $/1M | Цена Output $/1M |
|--------|--------|----------|-----------------|------------------|
| `gemini-3.5-flash` | Stable | 1M | $1.50 | $9.00 |
| `gemini-3.1-pro-preview` | Preview | 1M | $2.00 | $12.00 |
| `gemini-3.1-flash-lite` | Stable | 1M | $0.25 | $1.50 |
| `gemini-3.1-flash-lite-preview` | Preview | 1M | $0.25 | $1.50 |
| `gemini-3-flash-preview` | Preview | 1M | $0.50 | $3.00 |

### Gemini 2.5 (предыдущее поколение)

| Модель | Статус | Контекст | Цена Input $/1M | Цена Output $/1M |
|--------|--------|----------|-----------------|------------------|
| `gemini-2.5-pro` | Stable | 1M | $1.25 | $10.00 |
| `gemini-2.5-flash` | Stable | 1M | $0.30 | $2.50 |
| `gemini-2.5-flash-lite` | Stable | 1M | **$0.10** | **$0.40** |
| `gemini-2.5-flash-lite-preview` | Preview | 1M | $0.10 | $0.40 |

### Аудио-модели (Live API, TTS)

| Модель | Статус | Назначение | Input $/1M | Output $/1M |
|--------|--------|-----------|-----------|------------|
| `gemini-3.1-flash-live-preview` | Preview | Аудио-диалог реального времени (A2A) | $0.75 | $4.50 |
| `gemini-3.1-flash-tts-preview` | Preview | Text-to-Speech | $0.50 | $3.00 |
| `gemini-2.5-flash-native-audio-preview` | Preview | Bidirectional voice + video | $0.50 | $2.00 |
| `gemini-2.5-flash-preview-tts` | Preview | Text-to-Speech быстрый | $0.50 | $10.00 |
| `gemini-2.5-pro-preview-tts` | Preview | Text-to-Speech высокое качество | $0.50 | $10.00 |

---

## Ценовые тиры

| Tier | Скидка | Латентность |
|------|--------|------------|
| **Standard** | — | Стандартная |
| **Batch** | 50% | до 24 часов |
| **Flex** | 50% | Переменная |
| **Priority** | +80% к цене | Минимальная |

### Пример Batch pricing

```
Gemini 3.5 Flash:  Input $0.75 / Output $4.50  (вместо $1.50 / $9.00)
Gemini 2.5 Flash:  Input $0.15 / Output $1.25  (вместо $0.30 / $2.50)
```

---

## Free Tier

**5 000 промптов в месяц** — бесплатно, shared across Gemini 3 модели:
- Gemini 3.5 Flash — **free** (до лимита)
- Gemini 3.1 Flash-Lite — **free**
- Gemini 3 Flash Preview — **free**

После лимита — автоматическое переключение на Standard pricing.

---

## Аудио-возможности (для транскрипции)

Все Gemini 3 и 2.5 модели поддерживают **audio input** (кроме TTS-специализированных).

| Модель | ASR | TTS | Live Audio | Best for |
|--------|-----|-----|-----------|----------|
| Gemini 3.5 Flash | ✅ | ❌ | ❌ | Транскрипция + суммаризация |
| Gemini 3.1 Flash-Lite | ✅ | ❌ | ❌ | Дешёвая транскрипция |
| Gemini 3.1 Flash Live | ✅ | ✅ | ✅ | Реальное время |
| Gemini 3.1 Flash TTS | ❌ | ✅ | ❌ | Озвучка |
| Gemini 2.5 Flash Native Audio | ✅ | ✅ | ✅ | Видео + аудио агенты |

---

## Сравнение с текущими провайдерами

### Gemini 3.5 Flash

| Провайдер | Input | Output | Доступ |
|-----------|-------|--------|--------|
| **Google Direct** | $1.50 | $9.00 | Через `GEMINI_API_KEY` |
| OpenRouter | $1.50 | $9.00 | `openrouter/google/gemini-3.5-flash` |
| RouterAI | 138 ₽ | 833 ₽ | `routerai/google/gemini-3.5-flash` |

### Gemini 2.5 Flash-Lite (самый дешёвый)

| Провайдер | Input | Output | Доступ |
|-----------|-------|--------|--------|
| **Google Direct** | **$0.10** | **$0.40** | Через `GEMINI_API_KEY` |
| OpenRouter | $0.10 | $0.40 | `openrouter/google/gemini-2.5-flash` |
| RouterAI | 6 ₽ | 27 ₽ | `routerai/deepseek/deepseek-v4-flash` |

---

## Интеграция

### Через OpenRouter (уже работает, без ключа)

```
opencode run --model openrouter/google/gemini-3.5-flash "текст"
```

### Через RouterAI (дешевле, без ключа)

```
opencode run --model routerai/google/gemini-3.5-flash "текст"
```

### Через Google AI напрямую (нужен ключ)

```python
import google.generativeai as genai
genai.configure(api_key="GEMINI_API_KEY")
model = genai.GenerativeModel("gemini-3.5-flash")
response = model.generate_content("текст")
```

---

## Рекомендации для transcription pipeline

| Сценарий | Модель | Цена/1M | Через |
|----------|--------|---------|-------|
| ASR дешёвый | Gemini 2.5 Flash-Lite | $0.10/$0.40 | openrouter/routerai |
| ASR + суммаризация | Gemini 3.5 Flash | $1.50/$9.00 | openrouter/routerai |
| ASR качественный | Gemini 3.1 Pro | $2.00/$12.00 | openrouter/routerai |
| TTS | Gemini 3.1 Flash TTS | $0.50/$3.00 | Google Direct |
| Live Audio агент | Gemini 3.1 Flash Live | $0.75/$4.50 | Google Direct |
