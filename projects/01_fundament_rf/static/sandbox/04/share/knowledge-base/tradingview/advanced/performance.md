# Advanced Topics — Performance & Optimization

**Версия:** Lightweight Charts v5.2

## Оптимизация производительности

### Large Data Sets

При работе с большим количеством данных (10000+ свечей):

```javascript
// 1. Уменьшите barSpacing
chart.applyOptions({
    layout: {
        background: { type: 'solid', color: '#131722' },
    },
    grid: {
        vertLines: { visible: false },
        horzLines: { visible: false },
    },
});

// 2. Отключите ненужные элементы
chart.applyOptions({
    crosshair: {
        vertLine: { visible: false },
        horzLine: { visible: false },
    },
});

// 3. Используйте sampling для больших массивов
const sampledData = sampleData(originalData, 500); // оставить 500 точек
series.setData(sampledData);
```

### Memory Management

```javascript
// Удаляйте chart когда не нужен
function destroyChart() {
    if (chart) {
        chart.remove();
        chart = null;
    }
}

// Не создавайте новый chart в loop
// Вместо этого обновляйте данные
series.setData(newData); // заменяет все данные
series.update(newPoint); // добавляет/обновляет последнюю точку
```

### Efficient Updates

```javascript
// ❌ Плохо: полная перерисовка
setInterval(() => {
    const allData = fetchAllData();
    series.setData(allData);
}, 1000);

// ✅ Хорошо: инкрементальное обновление
setInterval(() => {
    const lastPoint = fetchLastPoint();
    series.update(lastPoint);
}, 1000);
```

### Canvas Rendering

Lightweight Charts использует Canvas для рендеринга. Для оптимизации:

```javascript
// Отключите antialiasing если не нужен
chart.applyOptions({
    renderer: {
        antialias: false,
    },
});

// Используйте фиксированный размер где возможно
chart.applyOptions({
    width: 800,
    height: 600,
    autoSize: false,
});
```

## Best Practices

| Практика | Описание |
|----------|----------|
| `update()` вместо `setData()` | Для real-time обновлений |
| Отключайте невидимые элементы | grid, crosshair если не нужны |
| Используйте ResizeObserver | Но не вызывайте resize слишком часто |
| Ограничивайте количество серий | Максимум 5-10 серий |
| Удаляйте chart | `chart.remove()` когда не нужен |

## Performance Tips

1. **Для 1000+ свечей:** отключите grid, используйте `update()` вместо `setData()`
2. **Для real-time:** ограничьте частоту обновлений до 1-2 секунд
3. **Для мобильных:** уменьшите `barSpacing`, отключите shadow DOM
4. **Для WebGL:** используйте аппаратное ускорение где возможно

## Версии

Lightweight Charts™ v3.8+, v4.x, v5.x
