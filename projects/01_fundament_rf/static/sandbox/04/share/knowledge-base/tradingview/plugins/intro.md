# Plugins — Custom Series and Primitives

**Версия:** Lightweight Charts v5.0+

## Когда использовать

Для создания **кастомных серий данных** или **примитивов** которых нет в стандартной библиотеке.

## Типы плагинов

| Тип | Интерфейс | Описание |
|-----|-----------|----------|
| Custom Series | `ICustomSeriesPaneView` | Кастомный тип серии (HLC, Heatmap, etc.) |
| Custom Renderer | `ICustomSeriesPaneRenderer` | Рендерер для custom series |
| Hit Test | `ICustomSeriesHitTestResult` | Обработка кликов |
| Series Primitive | `ISeriesPrimitive` | overlays, markers, shapes |
| Pane Primitive | `IPanePrimitive` | горизонтальные линии, background |

## Custom Series Plugin

### Структура плагина

```typescript
import { IChartApi, ISeriesApi, SeriesType, Time } from 'lightweight-charts';

interface CustomData {
    time: Time;
    value: number;
    color?: string;
}

class CustomSeriesView implements ICustomSeriesPaneView {
    renderer(): IPrimitivePaneRenderer {
        return new CustomRenderer();
    }
}

class CustomSeries implements ISeriesDefinition {
    name(): string { return 'custom'; }
    createSeries(api: IChartApi): ISeriesApi {
        return api.createCustomSeries(this, new CustomSeriesView());
    }
}
```

### Пример: Stacked Area (из plugin-examples)

```javascript
// Готовый пример: https://github.com/tradingview/lightweight-charts/tree/master/plugin-examples/src/plugins/stacked-area-series
import { createChart } from 'lightweight-charts';
import { StackedAreaSeries } from './stacked-area-series';

const chart = createChart(container);
const series = chart.addSeries(StackedAreaSeries, {
    lineWidth: 2,
    colors: ['#26a69a', '#2962FF', '#ef5350'],
});

series.setData([
    { time: '2024-01-01', values: [10, 20, 30] },
    { time: '2024-01-02', values: [15, 25, 35] },
]);
```

## Series Primitives

Для добавления маркеров, линий, форм поверх графика:

```typescript
import { ISeriesPrimitive, IChartApi } from 'lightweight-charts';

class PriceLinePrimitive implements ISeriesPrimitive {
    constructor(price: number, color: string) {
        this._price = price;
        this._color = color;
    }

    implemente(): ISeriesPrimitiveWrapper {
        return {
            paneViews: () => [new PriceLineView(this._price, this._color)],
        };
    }
}

// Использование
series.attachPrimitive(new PriceLinePrimitive(100, '#2962FF'));
```

## Полезные ресурсы

- [Plugin Examples GitHub](https://github.com/tradingview/lightweight-charts/tree/master/plugin-examples/src/plugins)
- [Custom Series Tutorial](https://tradingview.github.io/lightweight-charts/docs/plugins/intro)
- [Bands Indicator Example](https://github.com/tradingview/lightweight-charts/tree/master/plugin-examples/src/plugins/bands-indicator)

## Версии

Lightweight Charts™ v5.0+ (Plugin API)
