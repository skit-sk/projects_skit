# Locale i18n

## Когда использовать

Для **локализации** графика под конкретную страну/язык. Форматирование дат, чисел, времени.

## Ключевые параметры

```javascript
const chart = createChart(container, {
  localization: {
    locale: 'ru-RU',               // локаль
    dateFormat: 'dd/MM/yy',         // формат даты
    timeFormat: 'hh:mm:ss',         // формат времени
  },
  timeScale: {
    timeVisible: true,              // показывать время
    secondsVisible: false,          // скрыть секунды
  },
  width: 800,
  height: 400,
});
```

## Доступные локали

- `'en-US'` — English (US)
- `'ru-RU'` — Русский
- `'de-DE'` — Deutsch
- И другие стандартные BCP 47 локали

## Полный рабочий пример

См. `/tradingview-demos/conditions/locale-i18n/index.html`

## Версии

Lightweight Charts™ v4.0+, v5.x

## Ресурсы

- [Документация](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/LocalizationOptions)
