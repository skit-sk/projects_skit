# AutoSize Responsive

## Когда использовать

Когда график должен **автоматически адаптироваться** к размеру контейнера. Идеально для responsive дизайна.

## Ключевые параметры

```javascript
const chart = createChart(container, {
  autoSize: true,
  // width/height игнорируются если autoSize=true
  // но используются как fallback если ResizeObserver недоступен
});
```

## Особенности

- Использует `ResizeObserver` для отслеживания размера контейнера
- Если `ResizeObserver` недоступен — используется `width`/`height` как fallback
- Не работает с фиксированными размерами — контейнер должен иметь ненулевой размер

## Полный рабочий пример

См. `/tradingview-demos/conditions/autosize-responsive/index.html`

## Версии

Lightweight Charts™ v4.0+, v5.x

## Ресурсы

- [Документация](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/TimeChartOptions#autosize)
