# Краткое резюме анализа проектов

**Дата:** 2026-06-21

## Всего проектов: 11

| # | Проект | Тип | Статус интеграции в 01 |
|---|---|---|---|
| 01 | fundament_rf | Flask-хаб | — |
| 02 | graphs_candle | Flask | `/proxy/02/` → localhost:5002 |
| 03 | demo_charts_ascii | Flask | `/proxy/03/` → localhost:5003 |
| 04 | tradingview-demos | Static | `/static/sandbox/04/` |
| 05 | transcript | CLI | статус + лог |
| 06 | screenshots_project | Static | `/static/sandbox/06/` |
| 07 | tg_bot_aiforguest | Telegram bot | статус + лог |
| 08 | ofd_api | Flask Blueprint | ✅ `/ofd-api/` в 01 |
| 09 | model_catalog | JSON catalog | ✅ `/ai-models/` в 01 |
| 10 | max_bot | MAX bot | статус + лог |
| 11 | med_life | Data/Atlas | `/med-life/` Blueprint в 01 |

## Главные риски

1. **Безопасность (критично)**
   - `/ccxt-api/api/env-keys` отдаёт Bitget-секреты.
   - Path traversal в Viz Lab позволяет удалять/читать произвольные файлы.
   - CSRF GET `/delete/<obj_id>`.
   - MAX webhook без секрета.

2. **Стабильность (высоко)**
   - `state.json`, `task_state.json`, `storage.py` — read-modify-write без блокировок.
   - Параллельный `sync-all` пишет в общие JSON.

3. **Технический долг (высоко)**
   - Нет тестов.
   - Огромные модули (`handler.py` 2454 строки).
   - Массовое дублирование Bitget-клиентов и TG/MAX-ботов.

## Рекомендуемая стратегия

**Портал-навигатор** на базе `01_fundament_rf`:
- `/sandbox/` — карточки всех проектов.
- `/sandbox/health` — статус всех сервисов.
- `/proxy/<id>/` — iframe для Flask-проектов 02/03.
- `/static/sandbox/<id>/` — mount для статики 04/06.
- `/med-life/` — Atlas of Human / паспорт состояния пациента.
- Боты/CLI — статус + логи.
- Не мержить всё в монолит.

## Первые шаги

1. Закрыть критические security-риски.
2. Ввести атомарную работу с JSON.
3. Создать `shared/bitget_client.py` и `shared/bot_core/`.
4. Создать Blueprint `sandbox` и `proxy` в 01.
5. Смонтировать статику 04/06.
6. Создать Blueprint `med_life`.
7. Запустить 02/03/04/06 на отдельных портах.

## Файлы отчётов

- `docs/PROJECT_ANALYSIS_REPORT.md` — полный отчёт.
- `docs/sandbox/SANDBOX_PLAN.md` — детальный план песочницы.
- `docs/sandbox/UI_DESIGN_SYSTEM.md` — дизайн-система.
- `docs/sandbox/SANDBOX_REGISTRY.yaml` — реестр проектов.
- `docs/med_life/FLASK_INTEGRATION_PLAN.md` — интеграция Med Life.
- `docs/med_life/ATLAS_DESIGN.md` — концепция Атласа.
- `docs/med_life/DATA_MODEL.md` — модель данных.
- `docs/med_life/API_SPEC.md` — API спецификация.
