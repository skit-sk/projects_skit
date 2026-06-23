# 4. Custom Horizontal Scale (createChartEx)

## Когда использовать

Для **нестандартных данных**, где стандартная временная шкала не подходит. Позволяет определить кастомное поведение горизонтальной оси через `IHorzScaleBehavior`.

## Ключевые параметры

```javascript
// Кастомный IHorzScaleBehavior
class FibonacciHorzScaleBehavior {
  options() {
    return { from: 0, to: 13 };
  }

  createConverterToInternalObj(scaleService) {
    return (time) => time;
  }

  createConverterFromInternalObj(scaleService) {
    return (index) => index;
  }

  formatLabel(scaleService, timestamp) {
    // Кастомное форматирование меток
    return timestamp.toString();
  }

  fillDatesForRange(baseTime, startIndex, endIndex, startDate) {
    // Заполнение данных для диапазона
    return [];
  }
}

const chart = createChartEx(container, new FibonacciHorzScaleBehavior(), options);
```

## Функция

```javascript
createChartEx(container, horzScaleBehavior, options)
```

- **container**: `HTMLElement` или `string`
- **horzScaleBehavior**: `THorzScaleBehavior` — кастомное поведение шкалы
- **options**: любые опции чарта

## Возвращает

`IChartApiBase<HorzScaleItem>` — базовый интерфейс (без методов timeScale())

## Особенности

- Максимальная гибкость для кастомных горизонтальных шкал
- Необходимо самостоятельно реализовать `IHorzScaleBehavior`
- Для стандартных случаев лучше использовать `createChart()`

## Полный рабочий пример

См. `/tradingview-demos/chart-types/4-custom-horizontal-scale/index.html`

## Версии

Lightweight Charts™ v4.0+

## Ресурсы

- [Документация](https://tradingview.github.io/lightweight-charts/docs/chart-types#custom-horizontal-scale-chart)
- [IHorzScaleBehavior API](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/IHorzScaleBehavior)
