# Project Links Matrix

Матрица связей между проектами workspace.

| От \ К | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **01** | — | proxy | proxy | static | — | static | HTTP-in | blueprint | blueprint | HTTP-in | blueprint |
| **02** | — | — | — | — | — | — | — | — | — | — | — |
| **03** | fallback | — | — | — | — | — | — | — | — | — | — |
| **04** | — | — | — | — | — | — | — | — | — | — | — |
| **05** | — | — | — | — | — | — | data-out | — | data | — | — |
| **06** | — | — | — | — | — | — | — | — | — | — | — |
| **07** | HTTP | — | — | — | data-in | — | — | shared_path | data | — | — |
| **08** | blueprint | — | — | — | — | — | shared_path | — | — | — | — |
| **09** | — | — | — | — | — | — | — | — | — | — | — |
| **10** | HTTP | — | — | — | — | — | shared_path | — | data | — | — |
| **11** | — | — | — | — | — | — | — | — | — | — | — |

## Легенда

| Тип | Описание |
|---|---|
| `proxy` | Flask reverse-proxy через `/proxy/<id>/` |
| `static` | Статический mount через `/static/sandbox/<id>/` |
| `blueprint` | Flask blueprint зарегистрирован в `01` |
| `HTTP` | Исходящий HTTP-вызов |
| `HTTP-in` | Входящий HTTP-вызов от бота |
| `data` | Чтение/запись общих данных |
| `data-in` / `data-out` | Направление потока данных |
| `fallback` | Fallback на данные другого проекта |
| `shared_path` | Общий модуль через `sys.path` |

## Связанные KB

- [Архитектура workspace](architecture-overview.md)
- [Реестр модулей](module-registry.md)
