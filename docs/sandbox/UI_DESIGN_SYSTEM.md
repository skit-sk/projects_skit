# Единая дизайн-система

## 1. Цель

Унифицировать визуальный язык всех проектов, начиная с `01_fundament_rf`, и обеспечить основу для песочницы.

## 2. Базовые токены

```css
:root {
  --color-bg: #0b0d10;
  --color-surface: #161b22;
  --color-surface-raised: #1c2128;
  --color-border: #30363d;
  --color-text: #c9d1d9;
  --color-text-muted: #8b949e;
  --color-accent: #58a6ff;
  --color-success: #238636;
  --color-danger: #f85149;
  --color-warning: #d29922;
  --color-info: #2f81f7;

  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;

  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;

  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.4);
}

[data-theme="light"] {
  --color-bg: #ffffff;
  --color-surface: #f6f8fa;
  --color-surface-raised: #ffffff;
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-muted: #57606a;
}
```

## 3. Компоненты

### Card

```css
.ui-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  box-shadow: var(--shadow-sm);
}
```

### KPI

```css
.ui-kpi {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
.ui-kpi__value {
  font-size: 1.5rem;
  font-weight: 600;
  font-family: var(--font-mono);
}
.ui-kpi__label {
  color: var(--color-text-muted);
  font-size: 0.875rem;
}
```

### Table

```css
.ui-table {
  width: 100%;
  border-collapse: collapse;
}
.ui-table th,
.ui-table td {
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid var(--color-border);
  text-align: left;
}
.ui-table th {
  color: var(--color-text-muted);
  font-weight: 500;
}
```

### Button

```css
.ui-button {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface-raised);
  color: var(--color-text);
  cursor: pointer;
}
.ui-button--primary {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: #fff;
}
.ui-button:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
```

### Tabs

```css
.ui-tabs {
  display: flex;
  gap: var(--space-sm);
  border-bottom: 1px solid var(--color-border);
}
.ui-tab {
  padding: var(--space-sm) var(--space-md);
  color: var(--color-text-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
}
.ui-tab--active {
  color: var(--color-text);
  border-color: var(--color-accent);
}
```

### Chart Container

```css
.ui-chart-container {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  min-height: 300px;
}
```

## 4. Layout

- Mobile-first.
- CSS Grid / Flexbox.
- Breakpoints: `xs < 400`, `sm < 600`, `md < 900`, `lg < 1200`.

```css
.ui-grid {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}
```

## 5. Accessibility

- Semantic HTML: `<nav>`, `<main>`, `<section>`, `<button>`.
- `aria-label`, `aria-expanded`, `aria-live` для динамики.
- `focus-visible` вместо `outline: none`.
- Контраст >= 4.5:1.
- `<label>` для всех полей ввода.

## 6. Типографика

```css
body {
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 1.5;
  color: var(--color-text);
  background: var(--color-bg);
}
code, pre {
  font-family: var(--font-mono);
}
```

## 7. Статусные индикаторы

```css
.ui-status--up { color: var(--color-success); }
.ui-status--down { color: var(--color-danger); }
.ui-status--warning { color: var(--color-warning); }
.ui-status--unknown { color: var(--color-text-muted); }
```

## 8. Storybook / Viz Lab

Разделы `/viz-lab/`:
1. Typography
2. Colors
3. Buttons
4. Cards
5. KPI blocks
6. Tables
7. Forms
8. Tabs
9. Modal
10. Plotly chart
11. SVG chart
12. ASCII art
13. TradingView widget
14. Theme switching demo

## 9. Миграция

1. Зафиксировать токены в `01/static/css/style.css`.
2. Создать компоненты-классы.
3. Переписать `index.html` и `card.html` — убрать inline-стили.
4. Распространить на 02, 03, 08 через shared CSS.
5. Добавить accessibility-атрибуты.
