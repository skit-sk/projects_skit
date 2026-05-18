# asciichart

```bash
pip install asciichart
```

Линейные графики в ASCII. Минимум зависимостей.

## Line chart

```python
import asciichart
print(asciichart.plot([0.4064, 0.4012, 0.4072, 0.4278, 0.4388]))
```

## Multi-series

```python
print(asciichart.plot([close, high]))
```

## Настройки

```python
asciichart.plot(data, {
    'height': 15,           # высота
    'format': '{:8.4f}',    # формат чисел
    'min': 0.35,            # min Y
    'max': 0.55,            # max Y
    'colors': ['red'],      # цвета (терминал)
})
```

## Ограничения

- Только line chart
- Нет цвета
- Нет подписей осей
- Нет дат
