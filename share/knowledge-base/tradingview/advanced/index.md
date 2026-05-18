# Advanced Charts

**Документация:** https://www.tradingview.com/charting-library-docs/

⚠️ **Важно:** Advanced Charts требует доступа к private repository TradingView.

## Описание

Advanced Charts — это полнофункциональная библиотека TradingView с:
- Полным набором технических индикаторов
- Инструментами рисования
- Annotation системой
- Multi-chart layouts
- Полной интеграцией с TradingView ecosystem

## Требования

| Требование | Описание |
|------------|----------|
| Доступ к private repo | Нужно запросить у TradingView |
| Лицензия | Commercial |
| Поддержка | От TradingView |

## Запрос доступа

1. Напишите на charting@tradingview.com
2. Опишите ваш use case
3. Получите credentials для доступа к private repository

## Структура private repo

После получения доступа вы получите доступ к:

```
charting_library/
├── README.md
├── charting_library.min.js    # Production build
├── charting_library.js       # Development build
├── images/
├── user_default_options.json
└── examples/
```

## Быстрый старт (после получения доступа)

```html
<div id="chart_container"></div>
<script src="charting_library.min.js"></script>
<script>
const widget = new TradingView.widget({
    symbol: 'AAPL',
    interval: 'D',
    container: 'chart_container',
    datafeed: new Datafeeds.UDFCompatibleDatafeed(),
    library_path: './charting_library/',
    locale: 'en',
    fullscreen: true,
    autosize: true
});
</script>
```

## Отличия от Lightweight Charts

| Функция | Lightweight Charts | Advanced Charts |
|---------|-------------------|-----------------|
| Размер | 35 KB | ~1 MB |
| Индикаторы | Нужно писать | 100+ встроенных |
| Drawing Tools | Нет | Полный набор |
| Price Scale | Ограничен | Расширенный |
| Time Scale | Базовый | Расширенный |
| Mobile | Да | Да |
| Режимы | Один график | Multi-chart |

## Известные фичи

- **Indicators:** Moving Averages, RSI, MACD, Bollinger Bands, Ichimoku, и 100+
- **Drawing Tools:** Trend lines, Channels, Fibonaccci, Gann, Shapes
- **Alerts:** Price, indicator, drawing alerts
- **Multi-chart:** Sync нескольких графиков
- **Trading:** Built-in trading panel (для broker integration)

## Ресурсы

- [Advanced Charts Demo](https://charting-library.tradingview-widget.com/)
- [TradingView Charting Library Docs](https://www.tradingview.com/charting-library-docs/)
- [GitHub Issues](https://github.com/tradingview/charting_library/issues) (требует доступа)

## Версия

Advanced Charts v30+ (private repository)
