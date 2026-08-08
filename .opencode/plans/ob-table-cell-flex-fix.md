# План исправления OB Table — `display: flex` на `<td>` ломает таблицу

## Диагностика

**Проблема:** Колонки таблицы сдвигаются, содержимое из одной `<td>` переливается в соседнюю. Шапка правильная (9 колонок), но значения не соответствуют заголовкам.

**Причина:** CSS устанавливает `display: flex` напрямую на `<td>` элементы:

```css
/* ccxt_api.css:1036-1044 — ПРОБЛЕМА */
.orderbook-table .ob-price-cell,
.orderbook-table .ob-vol-cell {
    display: flex;           /* ← <td> перестаёт быть table-cell */
    align-items: center;
    gap: 4px;
    padding: 2px 4px;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}
```

Когда `<td>` получает `display: flex`, он перестаёт корректно участвовать в табличном layout'е. Браузер не может правильно рассчитать ширину колонок, и содержимое одной ячейки наезжает на соседнюю.

**HTML-структура правильная:** 9 `<th>` в хедере, 9 `<td>` в строках данных. Проблема исключительно в CSS.

---

## Решение

Не применять `display: flex` к самому `<td>`. Использовать внутренний `<div>`-обёртку с классом `.ob-cell-content`, которая будет flex-контейнером. `<td>` остаётся `table-cell`.

## Изменения

### 1. CSS — `ccxt_api.css`

#### Удалить (строки ~1035-1048):

```css
/* ===== OB Cell Split Structure ===== */
.orderbook-table .ob-price-cell,
.orderbook-table .ob-vol-cell {
    display: flex;           /* ← удалить */
    align-items: center;     /* ← удалить */
    gap: 4px;                /* ← удалить */
    padding: 2px 4px;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;     /* — оставить */
}

.orderbook-table .ob-price-cell {
    font-weight: 600;
}
```

#### Добавить после `.ob-table-collapsed`:

```css
.ob-cell-content {
    display: flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
}
```

---

### 2. JS — `ccxt_api.js`

#### А. Функция `setCellPrice(id, val, field)` ~строка 536

Добавить `<div class="ob-cell-content">` как внешнюю обёртку вокруг indicator и value:

```javascript
function setCellPrice(id, val, field) {
    const el = document.getElementById(id);
    if (!el) return;
    const old = el.dataset.val;
    if (old === String(val)) return;
    el.dataset.val = val;
    bufPush(field || id, val);
    el.innerHTML =
        '<div class="ob-cell-content">' +
            '<div id="' + id + '-i" class="ob-indicator">' +
                arrow(val, field || id) + sparkSVG(field || id, '100%') +
            '</div>' +
            '<div id="' + id + '-v" class="ob-value">' +
                '<span class="cell-value">' + fmtPrice(val) + '</span>' +
            '</div>' +
        '</div>';
}
```

#### Б. Функция `setCellVol(id, val, field)` ~строка 573

```javascript
function setCellVol(id, val, field) {
    const el = document.getElementById(id);
    if (!el) return;
    const old = el.dataset.val;
    if (old === String(val)) return;
    el.dataset.val = val;
    bufPush(field || id, val);
    el.innerHTML =
        '<div class="ob-cell-content">' +
            '<div id="' + id + '-v" class="ob-value flash-on-update">' +
                '<span class="cell-value">' + fmt(val) + '</span>' +
            '</div>' +
            '<div id="' + id + '-i" class="ob-indicator">' +
                arrow(val, field || id) + sparkSVG(field || id, '100%') +
            '</div>' +
        '</div>';
    flashCellValue(id);
}
```

#### В. Initial render — template literals ~строки 924-941

Обернуть содержимое внутрь `<td class="ob-price-cell">` и `<td class="ob-vol-cell">` в `<div class="ob-cell-content">`:

```javascript
${b[0] ? `<td class="ob-price-cell" id="ob-bid-p-${i}" data-val="">
    <div class="ob-cell-content">
        <div id="ob-bid-p-${i}-i" class="ob-indicator">${arrow(b[0], 'ob_bid_p_'+i)}${sparkSVG('ob_bid_p_'+i, '100%')}</div>
        <div id="ob-bid-p-${i}-v" class="ob-value"><span class="cell-value">${fmtPrice(b[0])}</span></div>
    </div>
</td>` : `<td class="ob-price-cell" id="ob-bid-p-${i}" data-val="">—</td>`}
${b[1] ? `<td class="ob-vol-cell" id="ob-bid-v-${i}" data-val="">
    <div class="ob-cell-content">
        <div id="ob-bid-v-${i}-v" class="ob-value flash-on-update"><span class="cell-value">${fmt(b[1])}</span></div>
        <div id="ob-bid-v-${i}-i" class="ob-indicator">${arrow(b[1], 'ob_bid_v_'+i)}${sparkSVG('ob_bid_v_'+i, '100%')}</div>
    </div>
</td>` : `<td class="ob-vol-cell" id="ob-bid-v-${i}" data-val="">—</td>`}
${a[0] ? `<td class="ob-price-cell" id="ob-ask-p-${i}" data-val="">
    <div class="ob-cell-content">
        <div id="ob-ask-p-${i}-i" class="ob-indicator">${arrow(a[0], 'ob_ask_p_'+i)}${sparkSVG('ob_ask_p_'+i, '100%')}</div>
        <div id="ob-ask-p-${i}-v" class="ob-value"><span class="cell-value">${fmtPrice(a[0])}</span></div>
    </div>
</td>` : `<td class="ob-price-cell" id="ob-ask-p-${i}" data-val="">—</td>`}
${a[1] ? `<td class="ob-vol-cell" id="ob-ask-v-${i}" data-val="">
    <div class="ob-cell-content">
        <div id="ob-ask-v-${i}-v" class="ob-value flash-on-update"><span class="cell-value">${fmt(a[1])}</span></div>
        <div id="ob-ask-v-${i}-i" class="ob-indicator">${arrow(a[1], 'ob_ask_v_'+i)}${sparkSVG('ob_ask_v_'+i, '100%')}</div>
    </div>
</td>` : `<td class="ob-vol-cell" id="ob-ask-v-${i}" data-val="">—</td>`}
```

---

## Сводка изменений по файлам

| Файл | Изменение | Строки |
|------|-----------|--------|
| `ccxt_api.css` | Удалить `display: flex` с `.ob-price-cell`, `.ob-vol-cell` | ~1036-1048 |
| `ccxt_api.css` | Добавить `.ob-cell-content { display: flex; ... }` | после ~1033 |
| `ccxt_api.js` | `setCellPrice()` — обернуть в `.ob-cell-content` | ~536-571 |
| `ccxt_api.js` | `setCellVol()` — обернуть в `.ob-cell-content` | ~573-600 |
| `ccxt_api.js` | Initial render — 4 места обернуть в `.ob-cell-content` | ~924-941 |

---

## Ожидаемый результат

```html
<!-- Было (сломанное): -->
<td class="ob-price-cell" style="display:flex">...content...</td>

<!-- Стало (рабочее): -->
<td class="ob-price-cell">
    <div class="ob-cell-content" style="display:flex">
        ...content...
    </div>
</td>
```

`<td>` остаётся `table-cell` и участвует в табличном layout. Flex-контейнер только внутри ячейки.
