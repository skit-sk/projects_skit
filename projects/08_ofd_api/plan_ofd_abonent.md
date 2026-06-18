# Plan: OFD Abonent Module

## Структура данных

```
data/ofd/{inn}/
├── inn_abonent.json              ← абонент + провайдер + сводка ККТ
├── inn_kkt_index.json            ← ККТ + ФН + totals per provider
├── inn_kkt_{rnm}.json            ← агрегаты по ККТ
├── fn_{fn}.json                  ← смены по ФН
├── fn_{fn}_daily.json            ← чеки по дням
└── items/
    ├── items_aggregated.json     ← товары агрегированные (при выгрузке)
    └── items_raw.json            ← товары хронологически (при выгрузке)
```

## Маршруты (Blueprint `ofd_abonent`)

| Маршрут | Метод | Описание |
|---------|-------|----------|
| `/ofd_abonent/` | GET | Главная страница |
| `/ofd_abonent/sync` | POST | Sync engine (period_from, period_to) |
| `/ofd_abonent/api/charts` | GET | Данные для графиков (period, rnm, fn) |
| `/ofd_abonent/export/xls` | GET | Выгрузка XLS |
| `/ofd_abonent/export/csv` | GET | Выгрузка CSV |

## Графики

2 графика (чеки + суммы) × 3 периода (день/неделя/месяц) × 2 режима (stacked/grouped)

### Цвета
- 🟢 Cash: `#22c55e`
- 🔵 Card: `#3b82f6`  
- 🟡 Return: `#eab308`
- 🔴 Errors: `#ef4444`

### Sync Engine
1. INN → TradePoints → KKT → FN → shifts → daily → receipts → items
2. Provider привязан к каждому FN
3. Агрегация totals по ККТ/ФН

## Приоритет реализации
1. Storage Layer
2. Blueprint + Sync Engine
3. Выгрузка XLS/CSV
4. Графики Plotly (stacked/grouped)
