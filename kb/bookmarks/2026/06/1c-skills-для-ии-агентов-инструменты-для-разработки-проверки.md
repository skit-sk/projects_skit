---
analyzed_at: '2026-06-04T11:54:25'
date: 2026-06-04 11:53:43
domain: share.google
language: ru
source: tg
status: complete
tags:
- 1С
- 1C:Enterprise
- ИИ-агенты
- AI-agents
- skills
- test-bridge
- HTTP-API
- BSL
- разработка
- автоматизация
- Codex
- Claude Code
title: '1C Skills для ИИ-агентов: инструменты для разработки, проверки и тестирования
  1С'
url: https://share.google/HZ5KSSnhcwpdegyIS
---

# 1C Skills для ИИ-агентов: инструменты для разработки, проверки и тестирования 1С

> URL: https://share.google/HZ5KSSnhcwpdegyIS

## Summary
Репозиторий из 82 специализированных skills для ИИ-агентов (Codex, Claude Code) по разработке на 1С:Предприятие. Ключевой компонент — codex-test-bridge, HTTP-расширение для тестовых баз, дающее агентам JSON API (metadata, query, ExecuteBSL, RenderExternalPrintForm и др.) для проверки работоспособности артефактов без COM и UI.

## Key Points
- 82 локальных skills в отдельных папках с SKILL.md, скриптами и evals
- Покрытие: конфигурации, расширения, метаданные, управляемые формы, роли, СКД, EPF/ERF, веб-публикация
- codex-test-bridge — HTTP-сервис для тестовых баз с JSON API поверх 1С
- API: Health, Metadata, Describe, Query, ExecuteBSL, CallCommonModule, WriteObject, GetObject, DeleteObject, RenderExternalPrintForm, RenderExternalReport
- Bridge решает проблему верификации: агент меняет XML → загружает в базу → проверяет runtime через HTTP
- Безопасность: только для локальных демо-баз, не для боевых
- Установка через ИИ-агента по README репозитория

## Entities
- **1C:Предприятие** (tech)
- **codex-test-bridge** (tech)
- **msrv-tech/skills** (org)
- **Codex** (tech)
- **Claude Code** (tech)
- **BSL** (tech)
- **Playwright** (tech)
- **Apache** (tech)

## Tags
- 1С
- 1C:Enterprise
- ИИ-агенты
- AI-agents
- skills
- test-bridge
- HTTP-API
- BSL
- разработка
- автоматизация
- Codex
- Claude Code

