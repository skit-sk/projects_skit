# termgraph

```bash
pip install termgraph
```

Гистограммы в терминале.

## Bar chart

```python
from termgraph import termgraph

data = {'Label1': 0.41, 'Label2': 0.40, 'Label3': 0.43}
termgraph(data)
```

## Из командной строки

```bash
termgraph data.dat --color {green,red} --width 50
```

## Параметры

| Параметр | Описание |
|----------|----------|
| `--color` | Цвета через запятую |
| `--width` | Ширина колонки |
| `--stacked` | Стопка |
| `--format` | Формат чисел |

## Ограничения

- Только bar chart
- Только горизонтальные
- Нет временных рядов
