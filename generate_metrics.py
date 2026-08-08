#!/usr/bin/env python3
"""Generate candle_full_metrics_extended from project01 trade data."""

import json, csv, os, hashlib, math
from datetime import datetime, timezone
from collections import OrderedDict

CARD_DIR = "projects/01_fundament_rf/data/card"
OUT_DIR = "data/tradeLLm"

# ─── Schema: 245 fields in 20 blocks ──────────────────────────────────

BLOCKS = [
    {"id": 1,  "name": "OHLCV / Идентификация",        "cat": "OHLCV",  "emoji": "🟢", "fields": []},
    {"id": 2,  "name": "OHLCV / Геометрия свечи",       "cat": "OHLCV",  "emoji": "🟢", "fields": []},
    {"id": 3,  "name": "OHLCV / Справедливая цена",      "cat": "OHLCV",  "emoji": "🟢", "fields": []},
    {"id": 4,  "name": "Flow / Потоки и дельта",         "cat": "Flow",   "emoji": "🔵", "fields": []},
    {"id": 5,  "name": "OI & Liq / Открытый интерес",    "cat": "OI_Liq", "emoji": "🟣", "fields": []},
    {"id": 6,  "name": "Trend / Трендовые индикаторы",   "cat": "Trend",  "emoji": "🟠", "fields": []},
    {"id": 7,  "name": "Oscillator / Осцилляторы",       "cat": "Osc",    "emoji": "🟡", "fields": []},
    {"id": 8,  "name": "Cluster / Кластерные данные",    "cat": "Cluster","emoji": "🔴", "fields": []},
    {"id": 9,  "name": "Signal / Сигнальные флаги",      "cat": "Signal", "emoji": "⚪", "fields": []},
    {"id": 10, "name": "Meta / Метаданные",              "cat": "Meta",   "emoji": "🟢", "fields": []},
    {"id": 11, "name": "Fibonacci Grid 2.0",             "cat": "Fibo",   "emoji": "⬜", "fields": []},
    {"id": 12, "name": "SMC / Smart Money Concepts",     "cat": "SMC",    "emoji": "⬜", "fields": []},
    {"id": 13, "name": "Wyckoff / CRT",                  "cat": "Wyckoff","emoji": "⬜", "fields": []},
    {"id": 14, "name": "Elliott Wave",                   "cat": "Elliott","emoji": "⬜", "fields": []},
    {"id": 15, "name": "Order Flow Advanced",            "cat": "OF_Adv", "emoji": "⬜", "fields": []},
    {"id": 16, "name": "OTE & Liquidity Zones",          "cat": "OTE",    "emoji": "⬜", "fields": []},
    {"id": 17, "name": "Sentiment",                      "cat": "Sentim", "emoji": "⬜", "fields": []},
    {"id": 18, "name": "On-Chain",                       "cat": "OnChain","emoji": "⬜", "fields": []},
    {"id": 19, "name": "Position Tracking",              "cat": "Pos",    "emoji": "⬜", "fields": []},
    {"id": 20, "name": "Confluence Score",               "cat": "Score",  "emoji": "⬜", "fields": []},
]

def define_schema():
    """Return list of all 245 fields with metadata."""
    F = []
    def add(block_id, name_ru, name_en, typ, desc, formula="", abbr="", avail="real"):
        F.append(dict(block_id=block_id, name_ru=name_ru, name_en=name_en,
                       typ=typ, desc=desc, formula=formula, abbr=abbr, avail=avail))

    # Block 1: OHLCV Identification (12)
    b = 1
    add(b, "ID свечи",          "candle_id",            "UInt64",         "Хэш от symbol + ts_open",                       abbr="cid")
    add(b, "Символ",            "symbol",               "String",         "Торговая пара",                                  abbr="sym")
    add(b, "Таймфрейм",         "timeframe",            "String",         "'1m','5m','15m','1h','4h','1d'",                 abbr="tf")
    add(b, "Время открытия",    "ts_open",              "DateTime64(3)",  "Метка начала свечи UTC",                         abbr="ts_o")
    add(b, "Время закрытия",    "ts_close",             "DateTime64(3)",  "Метка конца свечи UTC",                          abbr="ts_c")
    add(b, "Цена открытия",     "open",                 "Decimal(18,8)",  "Первая сделка интервала",                        abbr="open")
    add(b, "Максимум",          "high",                 "Decimal(18,8)",  "Максимальная цена",                              abbr="high")
    add(b, "Минимум",           "low",                  "Decimal(18,8)",  "Минимальная цена",                               abbr="low")
    add(b, "Цена закрытия",     "close",                "Decimal(18,8)",  "Последняя сделка",                               abbr="close")
    add(b, "Объем базовый",     "volume_base",          "Decimal(18,8)",  "Объем в базовой валюте",                         abbr="vol_b")
    add(b, "Объем котировочный","volume_quote",         "Decimal(18,8)",  "Объем в USDT",                                   abbr="vol_q")
    add(b, "Кол-во тиков",      "ticks_count",          "UInt32",         "Сделок внутри свечи",                            abbr="tick", avail="external_api")

    # Block 2: Candle Geometry (10)
    b = 2
    add(b, "Размер тела",          "body_size",         "Decimal(18,8)",  "abs(close-open)",                               formula="abs(c-o)", abbr="b_sz")
    add(b, "Направление тела",     "body_direction",    "Int8",           "1=бычье, -1=медвежье, 0=доджи",                abbr="b_dir")
    add(b, "Верхняя тень",         "upper_wick",        "Decimal(18,8)",  "high - max(open,close)",                        formula="h-max(o,c)", abbr="u_wk")
    add(b, "Нижняя тень",          "lower_wick",        "Decimal(18,8)",  "min(open,close) - low",                         formula="min(o,c)-l", abbr="l_wk")
    add(b, "Полный диапазон",      "range_hl",          "Decimal(18,8)",  "high - low",                                    formula="h-l", abbr="rng")
    add(b, "Диапазон тела",        "range_co",          "Decimal(18,8)",  "close - open (со знаком)",                      formula="c-o", abbr="r_co")
    add(b, "Тело / диапазон",      "body_to_range",     "Decimal(9,4)",   "body_size / range_hl",                          formula="b_sz/r_hl", abbr="b2r")
    add(b, "Верхняя тень / диапазон","upper_wick_ratio","Decimal(9,4)",   "upper_wick / range_hl",                         formula="u_wk/r_hl", abbr="uwr")
    add(b, "Нижняя тень / диапазон","lower_wick_ratio", "Decimal(9,4)",   "lower_wick / range_hl",                         formula="l_wk/r_hl", abbr="lwr")
    add(b, "Тип свечи",            "candle_pattern",   "String",         "'doji','marubozu','hammer','shooting_star','spinning_top','generic'", abbr="c_pat")

    # Block 3: Fair Price & Volume (8)
    b = 3
    add(b, "VWAP",                "vwap",              "Decimal(18,8)",  "(high+low+close)/3 * volume / sum(vol)",        formula="(h+l+c)/3*V/ΣV", abbr="vwap", avail="computed")
    add(b, "TWAP (аппрокс.)",     "twap",              "Decimal(18,8)",  "(open+high+low+close)/4",                       formula="(o+h+l+c)/4", abbr="twap", avail="computed")
    add(b, "Медианная цена",      "median_price",      "Decimal(18,8)",  "(high+low)/2",                                  formula="(h+l)/2", abbr="mp", avail="computed")
    add(b, "Типичная цена",       "typical_price",     "Decimal(18,8)",  "(high+low+close)/3",                            formula="(h+l+c)/3", abbr="tp", avail="computed")
    add(b, "Отклонение от VWAP",  "deviation_vwap",    "Decimal(9,4)",   "(close-vwap)/vwap*100",                         formula="(c-vwap)/vwap*100", abbr="dvap", avail="computed")
    add(b, "Объем / SMA20",       "volume_ratio_20",   "Decimal(9,4)",   "volume / SMA(volume,20)",                       abbr="vr20", avail="external_api")
    add(b, "Объем / SMA50",       "volume_ratio_50",   "Decimal(9,4)",   "volume / SMA(volume,50)",                       abbr="vr50", avail="external_api")
    add(b, "Аномалия объема",     "volume_anomaly_flag","Int8",          "1 если volume_ratio_20 > 2.0",                  abbr="vanom", avail="external_api")

    # Block 4: Flow (8) - all NULL
    b = 4
    for (ru, en, typ, desc, abbr) in [
        ("Дельта объема",        "volume_delta",              "Decimal(18,8)", "Sum(Size_buy)-Sum(Size_sell)", "v_dlt"),
        ("Объем покупок (тейкер)","taker_buy_volume",         "Decimal(18,8)", "Агрессивные покупки", "tb_vol"),
        ("Объем продаж (тейкер)", "taker_sell_volume",        "Decimal(18,8)", "Агрессивные продажи", "ts_vol"),
        ("Чистый денежный поток", "net_flow_quote",           "Decimal(18,8)", "taker_buy_quote - taker_sell_quote", "nflw"),
        ("Дисбаланс потока",      "flow_imbalance",           "Decimal(9,4)",  "net_flow / volume_quote (-1..1)", "f_imb"),
        ("Коэфф. покупок",        "taker_buy_ratio",          "Decimal(9,4)",  "taker_buy / volume_base (0..1)", "tbr"),
        ("Объем нетто",           "volume_net",               "Decimal(18,8)", "volume_base - wash", "v_net"),
        ("Накопл. дельта (сессия)","cumulative_delta_session", "Decimal(18,8)", "С начала сессии", "cdlt_s"),
    ]:
        add(b, ru, en, typ, desc, abbr=abbr, avail="null")

    # Block 5: OI & Liq (9) - all NULL
    b = 5
    for (ru, en, typ, desc, abbr) in [
        ("Открытый интерес",        "open_interest",      "Decimal(18,8)", "OI на close", "oi"),
        ("Дельта OI",               "oi_delta",           "Decimal(18,8)", "OI(close)-OI(open)", "oi_d"),
        ("Дельта OI %",             "oi_delta_pct",       "Decimal(9,4)",  "oi_delta/OI(open)*100", "oi_dp"),
        ("Ликвидации LONG",         "liq_long",           "Decimal(18,8)", "Принуд. закрытые лонги", "liq_l"),
        ("Ликвидации SHORT",        "liq_short",          "Decimal(18,8)", "Принуд. закрытые шорты", "liq_s"),
        ("Суммарные ликвидации",    "liq_total",          "Decimal(18,8)", "liq_long+liq_short", "liq_t"),
        ("Дисбаланс ликвидаций",    "liq_imbalance",      "Decimal(9,4)",  "(liq_long-liq_short)/liq_total", "liq_i"),
        ("Преобладание ликвидаций", "liq_dominance",      "String",        "'longs','shorts','neutral'", "liq_dom"),
        ("OI+Price интерпретация",  "oi_price_sentiment", "String",        "trend_continuation/...", "oi_sent"),
    ]:
        add(b, ru, en, typ, desc, abbr=abbr, avail="null")

    # Block 6: Trend (28)
    b = 6
    for (ru, en, typ, desc, abbr) in [
        ("EMA 9",           "ema_9",           "Decimal(18,8)", "Быстрая EMA", "ema9"),
        ("EMA 21",          "ema_21",          "Decimal(18,8)", "Среднесрочная EMA", "ema21"),
        ("EMA 50",          "ema_50",          "Decimal(18,8)", "Основная трендовая EMA", "ema50"),
        ("EMA 200",         "ema_200",         "Decimal(18,8)", "Долгосрочная EMA", "ema200"),
        ("SMA 20",          "sma_20",          "Decimal(18,8)", "Простая MA 20", "sma20"),
        ("SMA 50",          "sma_50",          "Decimal(18,8)", "Простая MA 50", "sma50"),
        ("SMA 200",         "sma_200",         "Decimal(18,8)", "Простая MA 200", "sma200"),
        ("Цена vs EMA 200", "price_vs_ema200", "Decimal(9,4)",  "(close-ema200)/ema200*100", "p_ema2"),
        ("Цена vs EMA 50",  "price_vs_ema50",  "Decimal(9,4)",  "(close-ema50)/ema50*100", "p_ema5"),
        ("MACD линия",      "macd_line",       "Decimal(18,8)", "EMA12-EMA26", "macd_l"),
        ("MACD сигнал",     "macd_signal",     "Decimal(18,8)", "EMA9 от macd_line", "macd_s"),
        ("MACD гистограмма", "macd_histogram", "Decimal(18,8)", "macd_line - macd_signal", "macd_h"),
        ("MACD гист. пред.", "macd_histogram_prev", "Decimal(18,8)", "Значение на пред. свече", "macd_hp"),
        ("BB верх",         "bb_upper",        "Decimal(18,8)", "SMA20+2*StdDev20", "bb_u"),
        ("BB низ",          "bb_lower",        "Decimal(18,8)", "SMA20-2*StdDev20", "bb_l"),
        ("BB ширина %",     "bb_width",        "Decimal(9,4)",  "(bb_u-bb_l)/sma20*100", "bb_w"),
        ("%B",              "bb_pct_b",        "Decimal(9,4)",  "(close-bb_l)/(bb_u-bb_l)", "bb_pb"),
        ("Parabolic SAR",   "sar",             "Decimal(18,8)", "Стоп-уровень SAR", "sar"),
        ("SAR направление", "sar_direction",   "Int8",          "1=лонг, -1=шорт", "sar_d"),
        ("ADX",             "adx",             "Decimal(9,4)",  "Сила тренда 0-100", "adx"),
        ("+DI",             "plus_di",         "Decimal(9,4)",  "Бычье направление", "pdi"),
        ("-DI",             "minus_di",        "Decimal(9,4)",  "Медвежье направление", "mdi"),
        ("Kumo Senkou A",   "kumo_a",          "Decimal(18,8)", "(Tenkan+Kijun)/2", "kum_a"),
        ("Kumo Senkou B",   "kumo_b",          "Decimal(18,8)", "(Max52+Min52)/2", "kum_b"),
        ("Kumo толщина %",  "kumo_thickness",  "Decimal(9,4)",  "abs(kum_a-kum_b)/close*100", "kum_t"),
        ("Цена vs Kumo",    "price_vs_kumo",   "String",        "'above','inside','below'", "p_kum"),
        ("Tenkan-sen",      "tenkan_sen",      "Decimal(18,8)", "(High9+Low9)/2", "tenk"),
        ("Kijun-sen",       "kijun_sen",       "Decimal(18,8)", "(High26+Low26)/2", "kiju"),
    ]:
        add(b, ru, en, typ, desc, abbr=abbr, avail="external_api")

    # Block 7: Oscillators (15)
    b = 7
    for (ru, en, typ, desc, abbr) in [
        ("RSI 7",           "rsi_7",           "Decimal(9,4)",  "Быстрый RSI", "rsi7"),
        ("RSI 14",          "rsi_14",          "Decimal(9,4)",  "Стандартный RSI", "rsi14"),
        ("RSI 21",          "rsi_21",          "Decimal(9,4)",  "Медленный RSI", "rsi21"),
        ("Stochastic %K",   "stoch_k",         "Decimal(9,4)",  "(14,3,3)", "st_k"),
        ("Stochastic %D",   "stoch_d",         "Decimal(9,4)",  "SMA3(%K)", "st_d"),
        ("Stochastic зона", "stoch_zone",      "String",        "overbought/oversold/neutral", "st_z"),
        ("CCI 20",          "cci_20",          "Decimal(9,4)",  "Commodity Channel", "cci"),
        ("MFI 14",          "mfi_14",          "Decimal(9,4)",  "Money Flow Index", "mfi"),
        ("OBV",             "obv",             "Decimal(18,8)", "On-Balance Volume", "obv"),
        ("OBV изменение",   "obv_delta",       "Decimal(18,8)", "Δ OBV", "obv_d"),
        ("ATR 14",          "atr_14",          "Decimal(18,8)", "Average True Range", "atr14"),
        ("ATR %",           "atr_pct",         "Decimal(9,4)",  "atr/close*100", "atr_p"),
        ("Current ATR ratio","current_atr_ratio","Decimal(9,4)", "range_hl/atr14", "catr_r"),
        ("RSI дивергенция", "rsi_divergence",  "Int8",          "1=бычья, -1=медвежья", "rsi_dv"),
        ("MFI дивергенция", "mfi_divergence",  "Int8",          "1=бычья, -1=медвежья", "mfi_dv"),
    ]:
        add(b, ru, en, typ, desc, abbr=abbr, avail="external_api")

    # Block 8: Cluster (16) - all NULL
    b = 8
    for (ru, en, typ, desc, abbr) in [
        ("POC цена",              "poc_price",             "Decimal(18,8)", "Цена макс. объема", "poc"),
        ("POC vs Close",          "poc_vs_close",          "Decimal(9,4)",  "(close-poc)/range_hl", "poc_vc"),
        ("Объем на POC",          "poc_volume",            "Decimal(18,8)", "Суммарный объем на POC", "poc_v"),
        ("VAH (70%)",             "vah",                   "Decimal(18,8)", "Value Area High", "vah"),
        ("VAL (70%)",             "val",                   "Decimal(18,8)", "Value Area Low", "val"),
        ("VA ширина %",           "va_width_pct",          "Decimal(9,4)",  "(vah-val)/close*100", "va_w"),
        ("Close vs VA",           "close_va_position",     "String",        "above_vah/below_val/inside", "c_va"),
        ("Дельта на close",       "delta_close",           "Decimal(18,8)", "Кумулятивная дельта на close", "d_cls"),
        ("Макс. дельта",          "max_delta",             "Decimal(18,8)", "Пик дельты (покупатели)", "max_d"),
        ("Мин. дельта",           "min_delta",             "Decimal(18,8)", "Пик дельты (продавцы)", "min_d"),
        ("Чистое изм. дельты",    "delta_net_change",      "Decimal(18,8)", "delta_close-delta_open", "d_net"),
        ("Скрытая дивергенция",   "hidden_divergence",     "String",        "bullish_hidden/...", "hd_div"),
        ("Уровней в профиле",     "profile_levels_count",  "UInt16",        "Уникальных цен внутри свечи", "prf_lv"),
        ("Топ-3 объема",          "top3_volume_levels",    "String",        "JSON [{price,vol}]", "t3vol"),
        ("Топ-3 дельты +",        "top3_delta_positive",   "String",        "JSON [{price,delta}]", "t3dp"),
        ("Топ-3 дельты -",        "top3_delta_negative",   "String",        "JSON [{price,delta}]", "t3dn"),
    ]:
        add(b, ru, en, typ, desc, abbr=abbr, avail="null")

    # Block 9: Signals (14) - all external_api
    b = 9
    for (ru, en, typ, desc, abbr) in [
        ("MACD пересечение сигнал","macd_signal_cross",   "Int8", "1=вверх, -1=вниз", "ms_cr"),
        ("MACD пересечение ноль",  "macd_zero_cross",     "Int8", "1=выше 0, -1=ниже", "mz_cr"),
        ("EMA 9/21 пересечение",   "ema_9_21_cross",      "Int8", "Золотой/Мёртвый крест", "e9_21"),
        ("EMA 50/200 пересечение", "ema_50_200_cross",    "Int8", "Стратег. смена тренда", "e50200"),
        ("+DI/-DI пересечение",    "di_cross",            "Int8", "Смена напр. ADX", "di_cr"),
        ("Stochastic пересечение", "stoch_cross",         "Int8", "%K и %D", "st_cr"),
        ("BB Squeeze",             "bb_squeeze",          "Int8", "1=мин ширина за 20", "bb_sq"),
        ("Пробой BB вверх",        "bb_breakout_up",      "Int8", "close > bb_upper", "bb_bu"),
        ("Пробой BB вниз",         "bb_breakout_down",    "Int8", "close < bb_lower", "bb_bd"),
        ("Фрактал Уильямса",       "fractal",             "Int8", "1=верх, -1=низ", "fra"),
        ("Касание EMA 200",        "touched_ema200",      "Int8", "low<=ema200<=high", "t_em2"),
        ("Касание VAH/VAL",        "touched_va_boundary", "Int8", "Цена касалась границ VA", "t_va"),
        ("MACD дивергенция",       "macd_divergence",     "Int8", "Дивергенция MACD", "md_dv"),
        ("Композитный сигнал",     "composite_signal",    "Int8", "-3..+3 униф. сигналов", "cmp_s"),
    ]:
        add(b, ru, en, typ, desc, abbr=abbr, avail="external_api")

    # Block 10: Metadata (7)
    b = 10
    add(b, "День недели",       "day_of_week",      "UInt8",  "1-7 (пн-вс)",          abbr="dow",   avail="computed")
    add(b, "Час",               "hour",             "UInt8",  "0-23",                  abbr="hr",    avail="computed")
    add(b, "Сессия",            "session",          "String", "'asian','european','american','overlap'", abbr="sess", avail="computed")
    add(b, "Флаг перехода сессии","session_change",  "Int8",   "1=новая сессия",       abbr="s_ch",  avail="computed")
    add(b, "Спред биржи",       "bid_ask_spread",   "Decimal(9,4)", "avg spread %",    abbr="baspr", avail="external_api")
    add(b, "Время с последней", "time_since_last",  "UInt32", "Секунд с пред. свечи",   abbr="ts_lst", avail="computed")
    add(b, "Аномалия",          "is_anomaly",       "Int8",   "1=сбой/выброс",         abbr="anom",  avail="computed")

    # Block 11: Fibonacci Grid 2.0 (18)
    b = 11
    fibo_levels = [
        (2.618, "Ultra Expansion", "Глобальный тейк-профит", "fib_2618"),
        (1.618, "Golden Target", "Основная цель (TP3)", "fib_1618"),
        (1.130, "Hunt Zone", "Ложный пробой перед разворотом", "fib_hunt"),
        (1.000, "Swing Low", "Точка опоры (0% импульса)", "fib_1000"),
        (0.836, "Sniper Entry", "Максимально точный вход (High Prob)", "fib_snip"),
        (0.786, "Deep Discount", "Граница зоны OTE", "fib_786"),
        (0.705, "Sweet Spot", "Золотая середина входа по ICT", "fib_sweet"),
        (0.618, "Discount / OTE", "Начало зоны набора позиции", "fib_618"),
        (0.500, "Equilibrium", "Справедливая цена", "fib_equil"),
        (0.382, "Standard Retr", "Стандартный откат", "fib_382"),
        (0.236, "Shallow Retr", "Поверхностный откат", "fib_236"),
        (-0.136, "Wick Zone", "Снятие стопов за фитилями", "fib_wick"),
        (-0.272, "Liquidity Sweep", "Стандартный сбор ликвидности", "fib_swp"),
        (-0.445, "Whale Target", "Крупные лимитные заявки", "fib_whale"),
        (-0.705, "Negative OTE", "Экстремальное поглощение", "fib_negote"),
        (-0.809, "Hard Invalidation", "Безусловная отмена плана", "fib_hard"),
        (-1.000, "Full Cycle Sweep", "Полное поглощение диапазона", "fib_full"),
    ]
    for lvl, name, desc, abbr in fibo_levels:
        add(b, f"Fibo {lvl:+.3f} — {name}", f"fib_level_{str(lvl).replace('.','_').replace('-','neg_')}",
            "Decimal(18,8)", desc, formula=f"anchor_low + (anchor_high-anchor_low)*{lvl}", abbr=abbr, avail="computed")
    add(b, "Grid Anchor High",  "grid_anchor_high",  "Decimal(18,8)", "Верхний якорь сетки",   abbr="grd_h", avail="computed")
    add(b, "Grid Anchor Low",   "grid_anchor_low",   "Decimal(18,8)", "Нижний якорь сетки",    abbr="grd_l", avail="computed")
    # Note: we had 17 + 2 = 19, but plan said 18. Let's adjust anchors into existing fields.
    # Actually original plan had 20+ fields for Fibo. Keep it clean.

    # Block 12: SMC (14)
    b = 12
    smc_fields = [
        ("BOS направление",     "bos_direction",          "String", "BULLISH/BEARISH", "bos_d"),
        ("BOS уровень",         "bos_level",              "Decimal(18,8)", "Ценовой уровень BOS", "bos_lv"),
        ("CHoCH направление",   "choch_direction",        "String", "BULLISH/BEARISH", "choc_d"),
        ("CHoCH подтверждён",   "choch_confirmed",        "Int8", "0/1", "choc_c"),
        ("MSS направление",     "mss_direction",          "String", "BULLISH/BEARISH", "mss_d"),
        ("MSS displacement",    "mss_displacement",       "Decimal(18,8)", "ATR-фильтр", "mss_dp"),
        ("MSS подтверждён",     "mss_confirmed",          "Int8", "0/1", "mss_c"),
        ("OB тип",              "ob_type",                "String", "BULLISH/BEARISH", "ob_t"),
        ("OB high",             "ob_high",                "Decimal(18,8)", "Верхняя граница OB", "ob_h"),
        ("OB low",              "ob_low",                 "Decimal(18,8)", "Нижняя граница OB", "ob_l"),
        ("OB mitigated",        "ob_mitigated",           "Int8", "0/1", "ob_m"),
        ("FVG active count",    "fvg_active",             "UInt8", "Активных FVG", "fvg_ac"),
        ("Liquidity sweep",     "liquidity_sweep_detected","Int8", "0/1", "liqsw"),
        ("Breaker block",       "breaker_block_exists",   "Int8", "0/1", "brk_bl"),
    ]
    for ru, en, typ, desc, abbr in smc_fields:
        add(b, ru, en, typ, desc, abbr=abbr, avail="null")

    # Block 13: Wyckoff (8)
    b = 13
    wyck_fields = [
        ("Wyckoff фаза",          "wyckoff_phase",              "String", "A/B/C/D/E/DISTR", "wy_ph"),
        ("Spring обнаружен",      "wyckoff_spring_detected",    "Int8", "0/1", "wy_spr"),
        ("Spring уровень",        "wyckoff_spring_level",       "Decimal(18,8)", "", "wy_spl"),
        ("UTAD обнаружен",        "wyckoff_utad_detected",      "Int8", "0/1", "wy_utd"),
        ("UTAD уровень",          "wyckoff_utad_level",         "Decimal(18,8)", "", "wy_utl"),
        ("SOS обнаружен",         "wyckoff_sos_detected",       "Int8", "0/1", "wy_sos"),
        ("Volume confirmation",   "wyckoff_volume_confirmation","Int8", "0/1", "wy_vc"),
        ("CRT/AMD фаза",          "crt_amd_phase",              "String", "ACCUM/MANIP/DISTR", "crt_a"),
    ]
    for ru, en, typ, desc, abbr in wyck_fields:
        add(b, ru, en, typ, desc, abbr=abbr, avail="null")

    # Block 14: Elliott (5)
    b = 14
    for (ru, en, typ, desc, abbr) in [
        ("Wave count",          "elliott_wave_count",       "UInt8", "Текущий волновой счёт", "el_wc"),
        ("Wave type",           "elliott_wave_type",        "String", "IMPULSE/CORRECTIVE", "el_wt"),
        ("Wave degree",         "elliott_wave_degree",      "String", "GRAND_SUPER/.../MINOR", "el_wd"),
        ("Expanded Flat",       "elliott_expanded_flat",    "Int8", "0/1", "el_ef"),
        ("Wave position %",     "elliott_wave_position_pct","Decimal(9,4)", "% внутри волны", "el_wp"),
    ]:
        add(b, ru, en, typ, desc, abbr=abbr, avail="null")

    # Block 15: Order Flow Advanced (9)
    b = 15
    for (ru, en, typ, desc, abbr) in [
        ("CVD",                "cvd_value",            "Decimal(18,8)", "Cumulative Volume Delta", "cvd"),
        ("CVD дивергенция",    "cvd_divergence",       "Int8", "0/1", "cvd_dv"),
        ("Order Imbalance",    "order_imbalance",      "Decimal(9,4)", "-1..1", "ord_im"),
        ("BAVER",              "baver",                "Decimal(9,4)", "Bid-Ask Volume Exchange Ratio", "bavr"),
        ("Iceberg detected",   "iceberg_detected",     "Int8", "0/1", "iceb"),
        ("Iceberg count",      "iceberg_levels_count", "UInt8", "Кол-во iceberg-уровней", "iceb_n"),
        ("Stacked Imbalance",  "stacked_imbalance",    "Int8", "0/1", "stk_im"),
        ("Tape Speed",         "tape_speed",           "Decimal(9,4)", "Сделок/сек", "tap_sp"),
        ("Footprint mode",     "footprint_mode",       "String", "DELTA/VOLUME/BIDASK", "fp_md"),
    ]:
        add(b, ru, en, typ, desc, abbr=abbr, avail="null")

    # Block 16: OTE & Liq Zones (8)
    b = 16
    for (ru, en, typ, desc, abbr) in [
        ("OTE Range High",      "ote_range_high",           "Decimal(18,8)", "Максимум OTE диапазона", "ote_h"),
        ("OTE Range Low",       "ote_range_low",            "Decimal(18,8)", "Минимум OTE диапазона", "ote_l"),
        ("OTE 62% уровень",     "ote_level_62",             "Decimal(18,8)", "OTE 62%", "ote_62"),
        ("OTE 79% уровень",     "ote_level_79",             "Decimal(18,8)", "OTE 79%", "ote_79"),
        ("OTE Sweet Spot",      "ote_sweet_spot",           "Decimal(18,8)", "Sweet Spot цена", "ote_ss"),
        ("In OTE Zone",         "in_ote_zone",              "Int8", "0/1", "in_ote"),
        ("Nearest liq LONG",    "nearest_liquidation_long",  "Decimal(18,8)", "Ближ. ликв. пул лонгов", "nliq_l"),
        ("Nearest liq SHORT",   "nearest_liquidation_short", "Decimal(18,8)", "Ближ. ликв. пул шортов", "nliq_s"),
    ]:
        add(b, ru, en, typ, desc, abbr=abbr, avail="null")

    # Block 17: Sentiment (11)
    b = 17
    for (ru, en, typ, desc, abbr) in [
        ("Fear & Greed Index",    "fear_greed_index",      "UInt8", "0-100", "fgi"),
        ("F&G Classification",    "fear_greed_class",      "String", "EXTREME_FEAR/.../EXTREME_GREED", "fg_cls"),
        ("News Sentiment Score",  "news_sentiment_score",  "Decimal(5,4)", "-1..1", "news_s"),
        ("Social Volume",         "social_volume",         "UInt32", "Упоминаний", "soc_v"),
        ("Social Dominance %",    "social_dominance_pct",  "Decimal(9,4)", "%", "soc_d"),
        ("AltRank",               "altrank",               "UInt16", "AltRank", "alt_r"),
        ("Buzz Score",            "buzz_score",            "Decimal(9,4)", "Buzz", "buzz"),
        ("Put/Call Ratio",        "put_call_ratio",        "Decimal(9,4)", "PCR", "pcr"),
        ("Futures Basis %",       "futures_basis_pct",     "Decimal(9,4)", "%", "fut_b"),
        ("Long/Short Ratio",      "long_short_ratio",      "Decimal(9,4)", "L/S", "ls_r"),
        ("Estimated Leverage",    "estimated_leverage_ratio","Decimal(9,4)","ELR", "elr"),
    ]:
        add(b, ru, en, typ, desc, abbr=abbr, avail="null")

    # Block 18: On-Chain (16)
    b = 18
    for (ru, en, typ, desc, abbr) in [
        ("MVRV Ratio",           "mvrv_ratio",             "Decimal(9,4)", "MVRV", "mvrv"),
        ("SOPR",                 "sopr",                   "Decimal(9,4)", "SOPR", "sopr"),
        ("NVT Ratio",            "nvt_ratio",              "Decimal(9,4)", "NVT", "nvt"),
        ("Puell Multiple",       "puell_multiple",         "Decimal(9,4)", "Puell", "puel"),
        ("Large TX >$100K",      "large_tx_count_100k",    "UInt32", "Транзакций", "ltx1"),
        ("Large TX >$1M",        "large_tx_count_1m",      "UInt32", "Транзакций", "ltx2"),
        ("Large TX >$10M",       "large_tx_count_10m",     "UInt32", "Транзакций", "ltx3"),
        ("Whale Concentration %","whale_concentration_pct","Decimal(9,4)", "%", "wh_cn"),
        ("Exchange Netflow",     "exchange_netflow",       "Decimal(18,8)", "Чистый поток на биржи", "ex_nf"),
        ("Exchange Balance",     "exchange_balance",       "Decimal(18,8)", "Баланс бирж", "ex_bal"),
        ("Stablecoin Inflow",    "stablecoin_inflow",      "Decimal(18,8)", "Приток стейблов", "stbl_i"),
        ("BTC Reserve Risk",     "btc_reserve_risk",       "Decimal(9,4)", "Reserve Risk", "btc_rr"),
        ("Active Addresses",     "active_addresses",       "UInt32", "Активных адресов", "act_ad"),
        ("Coin Days Destroyed",  "coin_days_destroyed",    "Decimal(18,8)", "CDD", "cdd"),
        ("Avg Dormancy Days",    "average_dormancy_days",  "Decimal(9,4)", "Средний возраст монет", "dorm"),
        ("Whale Activity Level", "whale_activity_level",   "String", "LOW/MEDIUM/HIGH", "wh_act"),
    ]:
        add(b, ru, en, typ, desc, abbr=abbr, avail="null")

    # Block 19: Position Tracking (14)
    b = 19
    for (ru, en, typ, desc, abbr) in [
        ("Сторона позиции",       "position_side",         "String", "LONG/SHORT", "pside"),
        ("Кредитное плечо",       "leverage",              "Decimal(9,2)", "x", "lev"),
        ("Размер маржи",          "margin_size",           "Decimal(18,8)", "USDT", "mgn"),
        ("Стоимость позиции",     "position_value",        "Decimal(18,8)", "USDT", "pval"),
        ("Цена входа",            "entry_price",           "Decimal(18,8)", "USDT", "e_prc"),
        ("Нереализованный PnL",   "unrealized_pnl",        "Decimal(18,8)", "USDT", "upnl"),
        ("Нереализованный PnL %", "unrealized_pnl_pct",    "Decimal(9,4)", "%", "upnl_p"),
        ("Цена ликвидации",       "liquidation_price",     "Decimal(18,8)", "Liq price", "liq_pr"),
        ("Стоп-лосс",             "stop_loss_price",       "Decimal(18,8)", "SL цена", "sl_pr"),
        ("Тейк-профит",           "take_profit_price",     "Decimal(18,8)", "TP цена", "tp_pr"),
        ("Дней в позиции",        "days_open",             "UInt16", "Дней", "d_open"),
        ("ROE",                   "roe",                   "Decimal(9,4)", "Return on Equity %", "roe"),
        ("ROR",                   "ror",                   "Decimal(9,4)", "Return on Risk %", "ror"),
        ("Экспозиция %",          "exposure_pct",          "Decimal(9,4)", "% от портфеля", "exp_p"),
    ]:
        add(b, ru, en, typ, desc, abbr=abbr, avail="real")

    # Block 20: Confluence Score (15)
    b = 20
    for (ru, en, typ, desc, abbr) in [
        ("Score: Wyckoff Phase","score_wyckoff_phase",    "Int8", "+1 если фаза определена", "sc_wy"),
        ("Score: MSS",          "score_mss_confirmed",    "Int8", "+1 если MSS", "sc_mss"),
        ("Score: Liq Sweep",    "score_liquidity_sweep",  "Int8", "+1 если sweep", "sc_lsw"),
        ("Score: Value Area",   "score_value_area",       "Int8", "+1 если цена в VA", "sc_va"),
        ("Score: POI",          "score_poi",              "Int8", "+1 если цена у POI", "sc_poi"),
        ("Score: OTE",          "score_ote",              "Int8", "+1 если цена в OTE", "sc_ote"),
        ("Score: Heatmap",      "score_heatmap",          "Int8", "+1 если хитмап подтверждает", "sc_ht"),
        ("Score: OI Healthy",   "score_oi_healthy",       "Int8", "+1 если OI здоров", "sc_oi"),
        ("Score: Footprint",    "score_footprint",        "Int8", "+1 если футпринт подтверждает", "sc_fp"),
        ("Score: R/R OK",       "score_rr_ok",            "Int8", "+1 если R/R > 2", "sc_rr"),
        ("Confluence Total",    "confluence_total",       "UInt8", "Сумма 0-10", "cnf_t"),
        ("Confluence Count",    "confluence_count",       "UInt8", "Кол-во сигналов", "cnf_c"),
        ("Signal Grade",        "signal_grade",           "String", "WEAK/NEUTRAL/STRONG/CRITICAL", "sig_gr"),
        ("HTF Alignment",       "htf_alignment",          "Int8", "Совпадение с HTF", "htf_a"),
        ("Multi-TF Confluence", "mtf_confluence",         "UInt8", "Кол-во ТФ", "mtf"),
    ]:
        add(b, ru, en, typ, desc, abbr=abbr, avail="null")

    # Assign sequential global IDs and block local IDs
    gid = 0
    for blk in BLOCKS:
        lid = 0
        for f in F:
            if f["block_id"] == blk["id"]:
                gid += 1; lid += 1
                f["global_id"] = gid
                f["block_local_id"] = lid
                blk["fields"].append(f)

    return F, {b["id"]: b for b in BLOCKS}

# ─── Trade data loader ────────────────────────────────────────────────

def load_trades():
    """Load all 12 active trades from project01."""
    trades = []
    for entry in sorted(os.listdir(CARD_DIR)):
        dirpath = os.path.join(CARD_DIR, entry)
        if not os.path.isdir(dirpath) or entry.startswith("UNKNOWN") or entry == "ETH":
            continue
        # Find base JSON and _1D.json
        base_file = None; d1_file = None
        for fname in os.listdir(dirpath):
            fp = os.path.join(dirpath, fname)
            if fname.endswith(".json") and not fname.endswith("_1D.json") and not fname.endswith("_1h.json") and not fname.endswith("_4h.json") and not fname.endswith("_RAW.json"):
                base_file = fp
            elif fname.endswith("_1D.json"):
                d1_file = fp

        if not base_file:
            continue

        with open(base_file) as f:
            td = json.load(f)

        candles = []
        if d1_file and os.path.exists(d1_file):
            with open(d1_file) as f:
                d1 = json.load(f)
            candles = d1.get("candles", [])

        trades.append(dict(base=td, candles=candles, base_path=base_file, d1_path=d1_file))
    return trades

# ─── Metric computation ────────────────────────────────────────────────

def classify_candle_pattern(body_pct, wick_ratio, upper_wick, lower_wick, body_dir, range_hl):
    """Classify candle pattern with more types."""
    if range_hl == 0 or range_hl is None:
        return "doji"
    if body_pct < 0.05:
        return "doji"
    if body_dir == 0:
        return "doji"
    if body_pct > 0.90:
        return "marubozu"
    # Hammer: long lower shadow, small body, bullish
    lower_ratio = lower_wick / range_hl if range_hl else 0
    upper_ratio = upper_wick / range_hl if range_hl else 0
    if lower_ratio > 0.6 and upper_ratio < 0.1 and body_pct < 0.4:
        return "hammer" if body_dir > 0 else "inverted_hammer"
    if upper_ratio > 0.6 and lower_ratio < 0.1 and body_pct < 0.4:
        return "shooting_star" if body_dir < 0 else "inverted_hammer"
    if body_pct < 0.2:
        return "spinning_top"
    # Engulfing check needs previous candle - simplified
    if body_pct > 0.5 and upper_ratio < 0.15 and lower_ratio < 0.15:
        return "engulfing_like"
    return "generic"

def compute_metrics(trade, fields, sessions_info):
    """Compute all available metrics for one trade, one candle (last candle)."""
    base = trade["base"]["data"]
    candles = trade["candles"]
    entry = base.get("emoji_entry", {})
    live = base.get("live_position", {})
    emoji_upd = base.get("emoji_upd", {})

    symbol = entry.get("symbol", "?")
    ohlc_data = base.get("ohlc", {})
    cur_ohlc = ohlc_data.get("current", {})

    # Determine latest candle
    last_c = candles[-1] if candles else None

    values = {}

    # Build lookup by global_id
    fid_map = {}
    for f in fields:
        fid_map[f["name_en"]] = f
        values[f["global_id"]] = None

    def set_val(name_en, val):
        if name_en in fid_map:
            values[fid_map[name_en]["global_id"]] = val

    # ── Trade name for display ──
    trade_name = f"{symbol} #{entry.get('number','?')}"
    is_live_api = bool(live and live.get("hold_side"))
    has_live_data = bool(live)
    trade_type = "live_api" if is_live_api else ("live_poll" if has_live_data else "tracking")

    # ── Block 1: OHLCV ──
    if last_c:
        set_val("candle_id", f"{symbol}_1D_{last_c.get('date','?')}")
        set_val("symbol", symbol)
        set_val("timeframe", "1D")
        set_val("ts_open", last_c.get("datetime",""))
        set_val("ts_close", last_c.get("datetime",""))
        set_val("open", last_c.get("open"))
        set_val("high", last_c.get("high"))
        set_val("low", last_c.get("low"))
        set_val("close", last_c.get("close"))
        set_val("volume_base", last_c.get("volume"))
        set_val("volume_quote", last_c.get("quote_volume"))

        # ── Block 2: Geometry ──
        o = last_c.get("open", 0); h = last_c.get("high", 0)
        l = last_c.get("low", 0); c = last_c.get("close", 0)
        body_sz = abs(c - o)
        rng = h - l
        rng_co = c - o
        b_dir = 1 if c > o else (-1 if c < o else 0)
        u_wk = h - max(o, c)
        l_wk = min(o, c) - l

        set_val("body_size", round(body_sz, 8))
        set_val("body_direction", b_dir)
        set_val("upper_wick", round(u_wk, 8))
        set_val("lower_wick", round(l_wk, 8))
        set_val("range_hl", round(rng, 8))
        set_val("range_co", round(rng_co, 8))
        if rng > 0:
            set_val("body_to_range", round(body_sz/rng, 4))
            set_val("upper_wick_ratio", round(u_wk/rng, 4))
            set_val("lower_wick_ratio", round(l_wk/rng, 4))
        else:
            set_val("body_to_range", 0)
            set_val("upper_wick_ratio", 0)
            set_val("lower_wick_ratio", 0)
        body_pct = body_sz/rng if rng else 0
        pattern = classify_candle_pattern(body_pct, 0, u_wk, l_wk, b_dir, rng)
        set_val("candle_pattern", pattern)

        # ── Block 3: Fair price ──
        set_val("twap", round((o+h+l+c)/4, 8))
        set_val("median_price", round((h+l)/2, 8))
        set_val("typical_price", round((h+l+c)/3, 8))
        vwap_approx = ((h+l+c)/3) * last_c.get("volume", 0)
        set_val("vwap", round(vwap_approx, 8))
        if vwap_approx:
            set_val("deviation_vwap", round((c - vwap_approx)/vwap_approx*100, 4))

        # ── Block 10: Metadata ──
        dt = last_c.get("datetime", "")
        if dt:
            try:
                dto = datetime.fromisoformat(dt)
                set_val("day_of_week", dto.isoweekday())
                set_val("hour", dto.hour)
            except:
                pass
        sess_active = (last_c.get("sessions") or {}).get("active", [])
        session_str = ",".join(sess_active) if sess_active else "unknown"
        set_val("session", session_str)

    # ── Block 11: Fibonacci Grid 2.0 ──
    if last_c:
        fib = last_c.get("fibonacci", {})
        fib_levels = fib.get("levels", {})
        anchor_h = fib.get("high_price")
        anchor_l = fib.get("low_price")
        set_val("grid_anchor_high", anchor_h)
        set_val("grid_anchor_low", anchor_l)

        # Map standard fib keys to our schema
        fib_key_map = {
            "fib_level_0_0": fib_levels.get("0.0"),
            "fib_level_0_236": fib_levels.get("0.236"),
            "fib_level_0_382": fib_levels.get("0.382"),
            "fib_level_0_5": fib_levels.get("0.5"),
            "fib_level_0_618": fib_levels.get("0.618"),
            "fib_level_0_786": fib_levels.get("0.786"),
            "fib_level_1_0": fib_levels.get("1.0"),
            "fib_level_1_272": fib_levels.get("1.272"),
            "fib_level_1_414": fib_levels.get("1.414"),
            "fib_level_1_618": fib_levels.get("1.618"),
        }
        for fname, val in fib_key_map.items():
            set_val(fname, val)

        # Compute MidasFlow-specific levels from anchor
        if anchor_h is not None and anchor_l is not None:
            r = anchor_h - anchor_l
            mf_map = {
                2.618: "fib_level_2_618",
                1.130: "fib_level_1_130",
                0.836: "fib_level_0_836",
                0.705: "fib_level_0_705",
                -0.136: "fib_level_neg_0_136",
                -0.272: "fib_level_neg_0_272",
                -0.445: "fib_level_neg_0_445",
                -0.705: "fib_level_neg_0_705",
                -0.809: "fib_level_neg_0_809",
                -1.0: "fib_level_neg_1_0",
            }
            for level, fname in mf_map.items():
                set_val(fname, round(anchor_l + r * (1-level) if level < 0 else anchor_l + r * level, 8))

        # Standard retracements from existing levels
        set_val("fib_level_0_5", fib_levels.get("0.5") or (anchor_h + anchor_l)/2 if anchor_h and anchor_l else None)

    # ── Block 6: Trend (from ETH ETH indicator data) ──
    computed = base.get("computed", {})
    indicators = computed.get("indicators", {})
    if indicators.get("rsi") and len(indicators["rsi"]) > 0:
        rsi_vals = [v for v in indicators["rsi"] if v is not None]
        if rsi_vals:
            set_val("rsi_14", round(rsi_vals[-1], 4))
    macd = indicators.get("macd", {})
    if macd.get("macd") and len(macd["macd"]) > 0:
        macd_vals = [v for v in macd["macd"] if v is not None]
        sig_vals = [v for v in macd.get("signal", []) if v is not None]
        hist_vals = [v for v in macd.get("histogram", []) if v is not None]
        if macd_vals: set_val("macd_line", round(macd_vals[-1], 8))
        if sig_vals: set_val("macd_signal", round(sig_vals[-1], 8))
        if hist_vals: set_val("macd_histogram", round(hist_vals[-1], 8))
        if len(hist_vals) >= 2: set_val("macd_histogram_prev", round(hist_vals[-2], 8))

    # ── Block 19: Position Tracking ──
    leverage = base.get("leverage") or live.get("leverage")
    set_val("leverage", leverage)
    set_val("entry_price", entry.get("entry_price"))

    if live:
        set_val("position_side", live.get("hold_side", "long").upper())
        set_val("margin_size", live.get("margin_size"))
        set_val("position_value", live.get("position_value_usdt"))
        set_val("unrealized_pnl", live.get("unrealized_pl"))
        set_val("unrealized_pnl_pct", live.get("pl_percent"))
        set_val("liquidation_price", live.get("liquidation_price"))
        set_val("stop_loss_price", live.get("stop_loss_price"))
        set_val("take_profit_price", live.get("take_profit_price"))
        set_val("days_open", live.get("days_open"))
        roe_val = live.get("pl_percent")
        set_val("roe", roe_val)
        if live.get("margin_size") and live.get("margin_size") > 0:
            set_val("ror", round(live.get("unrealized_pl", 0) / live.get("margin_size") * 100, 4))
        set_val("exposure_pct", computed.get("exp_pct"))
    else:
        # Pure tracking trades (no live_position)
        set_val("position_side", "LONG")
        set_val("margin_size", entry.get("volume") or (live.get("margin_size")))
        set_val("unrealized_pnl", emoji_upd.get("pnl_usdt"))
        set_val("unrealized_pnl_pct", emoji_upd.get("pnl_percent"))
        set_val("roe", emoji_upd.get("pnl_percent"))
        stats = base.get("stats", {})
        set_val("days_open", stats.get("da"))

    # ── Block 10 extended: liq proximity from candle ──
    if last_c:
        liq_p = last_c.get("liq_proximity", {})
        if liq_p:
            # We can store these in a note - not a direct field but useful
            pass

    return values, trade_name, trade_type, symbol


# ─── Main generation ──────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    fields, blocks = define_schema()
    trades = load_trades()
    sessions_info = json.load(open("projects/01_fundament_rf/data/sessions_template.json"))

    print(f"[1] Loaded {len(trades)} trades, {len(fields)} schema fields")

    # Compute metrics for each trade
    all_trade_data = []
    for t in trades:
        vals, name, ttype, sym = compute_metrics(t, fields, sessions_info)
        all_trade_data.append(dict(
            name=name, type=ttype, symbol=sym, values=vals,
            base=t["base"]
        ))

    # ── JSON output ──
    json_out = {
        "schema_version": "2.0",
        "generated": datetime.now(timezone.utc).isoformat(),
        "description": "Unified candle_full_metrics_extended — 245 fields from qwest-tb.md + project01 trade data + tradellm specs",
        "total_fields": len(fields),
        "total_trades": len(all_trade_data),
        "blocks": [],
        "trades": [],
        "summary": {}
    }

    for blk in blocks.values():
        bf = [f for f in fields if f["block_id"] == blk["id"]]
        filled = sum(1 for f in bf if any(td["values"].get(f["global_id"]) is not None for td in all_trade_data))
        json_out["blocks"].append({
            "block_id": blk["id"],
            "name": blk["name"],
            "category": blk["cat"],
            "emoji": blk["emoji"],
            "total_fields": len(bf),
            "filled_fields": filled,
            "fields": [{
                "global_id": f["global_id"],
                "block_local_id": f["block_local_id"],
                "abbr": f["abbr"],
                "name_ru": f["name_ru"],
                "name_en": f["name_en"],
                "type": f["typ"],
                "description": f["desc"],
                "formula": f["formula"],
                "availability": f["avail"],
            } for f in bf]
        })

    for td in all_trade_data:
        trade_entry = {
            "trade_name": td["name"],
            "trade_type": td["type"],
            "symbol": td["symbol"],
            "fields": {}
        }
        for f in fields:
            gid = f["global_id"]
            v = td["values"].get(gid)
            if v is not None:
                trade_entry["fields"][f["name_en"]] = v
        json_out["trades"].append(trade_entry)

    # Summary
    live_api_trades = [td for td in all_trade_data if td["type"] == "live_api"]
    live_poll_trades = [td for td in all_trade_data if td["type"] == "live_poll"]
    tracking_trades = [td for td in all_trade_data if td["type"] == "tracking"]
    total_pnl = 0
    for td in all_trade_data:
        v = td["values"].get(fid_map_inner(fields, "unrealized_pnl"))
        if v is not None:
            total_pnl += v

    json_out["summary"] = {
        "total_trades": len(all_trade_data),
        "live_api_trades": len(live_api_trades),
        "live_poll_trades": len(live_poll_trades),
        "tracking_trades": len(tracking_trades),
        "profitable_count": sum(1 for td in all_trade_data if td["values"].get(fid_map_inner(fields, "unrealized_pnl_pct") or 0, -999) > 0),
        "total_pnl_usdt": round(total_pnl, 2),
        "total_fields_available": sum(1 for f in fields if any(td["values"].get(f["global_id"]) is not None for td in all_trade_data)),
        "total_fields_defined": len(fields),
        "coverage_pct": round(sum(1 for f in fields if any(td["values"].get(f["global_id"]) is not None for td in all_trade_data)) / len(fields) * 100, 1)
    }

    with open(f"{OUT_DIR}/candle_full_metrics_extended.json", "w", encoding="utf-8") as f:
        json.dump(json_out, f, ensure_ascii=False, indent=2)
    print(f"[2] JSON saved: {OUT_DIR}/candle_full_metrics_extended.json")

    # ── CSV output ──
    with open(f"{OUT_DIR}/candle_full_metrics_extended.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        header = ["block_id","block_name","category","global_id","block_local_id","abbr","name_ru","name_en","type","formula","availability"]
        header += [td["name"].replace(" ","_") for td in all_trade_data]
        writer.writerow(header)

        for fld in fields:
            row = [fld["block_id"], blocks[fld["block_id"]]["name"], blocks[fld["block_id"]]["emoji"],
                   fld["global_id"], fld["block_local_id"], fld["abbr"],
                   fld["name_ru"], fld["name_en"], fld["typ"], fld["formula"], fld["avail"]]
            for td in all_trade_data:
                v = td["values"].get(fld["global_id"])
                if v is None:
                    if fld["avail"] == "null":
                        row.append("NULL")
                    elif fld["avail"] in ("external_api", "computed"):
                        row.append(f"[{fld['typ']}]")
                    else:
                        row.append("")
                else:
                    row.append(str(v))
            writer.writerow(row)
    print(f"[3] CSV saved: {OUT_DIR}/candle_full_metrics_extended.csv")

    # ── MD output ──
    md_lines = []
    md_lines.append("# Candle Full Metrics Extended — Unified Data Table")
    md_lines.append(f"\n**245 fields × {len(all_trade_data)} trades** | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    md_lines.append(f"\n## Summary")
    md_lines.append(f"\n| Metric | Value |")
    md_lines.append(f"|--------|-------|")
    s = json_out["summary"]
    md_lines.append(f"| Total trades | {s['total_trades']} |")
    md_lines.append(f"| Live (Bitget API) | {s['live_api_trades']} |")
    md_lines.append(f"| Live (polled) | {s['live_poll_trades']} |")
    md_lines.append(f"| Tracking only | {s['tracking_trades']} |")
    md_lines.append(f"| Currently profitable | {s['profitable_count']} |")
    md_lines.append(f"| Total PnL USDT | {s['total_pnl_usdt']} |")
    md_lines.append(f"| Fields with data | {s['total_fields_available']} / {s['total_fields_defined']} ({s['coverage_pct']}%) |")

    md_lines.append(f"\n## Block Coverage\n")
    md_lines.append(f"| Block | Fields | Filled | Coverage |")
    md_lines.append(f"|-------|--------|--------|----------|")
    for blk in blocks.values():
        bf = [f for f in fields if f["block_id"] == blk["id"]]
        filled = sum(1 for f in bf if any(td["values"].get(f["global_id"]) is not None for td in all_trade_data))
        pct = round(filled/len(bf)*100) if len(bf) else 0
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        md_lines.append(f"| {blk['emoji']} {blk['name']} | {len(bf)} | {filled} | {bar} {pct}% |")

    # Trade-level data per block (compact)
    for blk in blocks.values():
        bf = [f for f in fields if f["block_id"] == blk["id"]]
        filled_any = any(any(td["values"].get(f["global_id"]) is not None for td in all_trade_data) for f in bf)
        if not filled_any:
            continue
        md_lines.append(f"\n### {blk['emoji']} Block {blk['id']}: {blk['name']}\n")
        # Table: field | abbreviation | type | availability | trade1 ... tradeN
        header = "| # | Abbr | Field | Type |"
        header += "|".join(td["name"][:12] for td in all_trade_data) + "|"
        md_lines.append(header)
        sep = "|---|-----|-------|------|" + "|".join("---" for _ in all_trade_data) + "|"
        md_lines.append(sep)
        for fld in bf:
            has_data = any(td["values"].get(fld["global_id"]) is not None for td in all_trade_data)
            if not has_data:
                continue
            row = f"| {fld['global_id']} | `{fld['abbr']}` | {fld['name_ru']} | `{fld['typ']}` |"
            for td in all_trade_data:
                v = td["values"].get(fld["global_id"])
                if v is None:
                    row += " — |"
                elif isinstance(v, float):
                    row += f" {v:.4f} |"
                else:
                    row += f" {v} |"
            md_lines.append(row)

    with open(f"{OUT_DIR}/candle_full_metrics_extended.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"[4] MD saved: {OUT_DIR}/candle_full_metrics_extended.md")

    return fields, blocks, all_trade_data, json_out

def fid_map_inner(fields, name_en):
    for f in fields:
        if f["name_en"] == name_en:
            return f["global_id"]
    return None

if __name__ == "__main__":
    main()
