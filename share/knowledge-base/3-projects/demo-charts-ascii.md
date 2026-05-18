# demo_charts_ascii — CLI-графики в Flask

**Расположение:** `projects/03_demo_charts_ascii/`

Демонстрационный проект для визуализации asciichart, plotext и termgraph через веб-интерфейс.

## Стек

```
Flask 3.x + Jinja2
asciichart       → ASCII-графики (.txt)
plotext 5.x      → цветные HTML-графики (.html + .txt)
termgraph 0.7.x  → гистограммы (.txt)
```

## Структура проекта

```
projects/03_demo_charts_ascii/
├── app.py                          # Flask entry: / (GET), /render (POST), /file/ (GET)
├── templates/
│   └── index.html                  # UI: файловое дерево + чекбоксы + панели вывода
├── static/css/
│   └── style.css                   # Тёмная тема (GitHub Dark)
├── generators/
│   ├── __init__.py
│   ├── asciichart_gen.py           # inline ASCII plot
│   ├── plotext_gen.py              # plotext: line/bar/scatter → .html + .txt
│   └── termgraph_gen.py            # termgraph: гистограмма → .txt
├── data/                           # копия projects/01_fundament_rf/data/card/ (10 символов)
│   ├── ADA_38a5c68d/
│   ├── API3_8fb2d418/
│   └── … (все 10)
├── outputs/                        # сгенерированные файлы
│   ├── asciichart/
│   ├── plotext/
│   └── termgraph/
└── requirements.txt
```

## Запуск

```bash
cd projects/03_demo_charts_ascii
pip install flask plotext termgraph
python3 app.py
# → http://localhost:5001
```

## Зависимости

```
Flask>=3.0
plotext>=5.0
termgraph>=0.5
asciichart не требуется (inline implementation)
```
