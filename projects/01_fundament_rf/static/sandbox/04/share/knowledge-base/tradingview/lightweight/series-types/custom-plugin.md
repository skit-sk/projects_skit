# Custom Series Plugin

## Когда использовать

Для создания **кастомных типов серий**, не предусмотренных библиотекой. Расширение функциональности через plugin API.

## Ключевые понятия

```typescript
// 1. Определяем кастомный класс, реализующий ICustomSeriesPaneView
class CustomSeriesPaneView implements ICustomSeriesPaneView {
  // 2. Методы для рисования
  draw(ctx: DrawContext, props: CustomSeriesPaneViewProps): void {
    // Кастомная логика отрисовки
  }

  // 3. Определение видимости
  isVisible(): boolean {
    return true;
  }
}

// 4. Регистрация и использование
chart.addCustomSeries(CustomSeriesPaneView, options);
```

## Интерфейсы

- `ICustomSeriesPaneView` — основной интерфейс для pane view
- `ICustomSeriesPaneRenderer` — рендерер для рисования
- `ICustomSeriesHitTestResult` — результат hit testing

## Особенности

- Полный контроль над отрисовкой
- Можно создавать собственные индикаторы и паттерны
- Документация: [Plugins](https://tradingview.github.io/lightweight-charts/docs/plugins/intro)

## Версии

Lightweight Charts™ v4.0+, v5.x

## Ресурсы

- [Документация](https://tradingview.github.io/lightweight-charts/docs/series-types#custom-series-plugins)
- [Plugins Intro](https://tradingview.github.io/lightweight-charts/docs/plugins/intro)
