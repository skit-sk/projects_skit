# PYTHON ENV Skill — Окружение

**Статус:** РАБОТАЕТ
**Обновлено:** 2026-05-05

## Активация venv

```bash
source venv/bin/activate
```

## Установленные пакеты

- `python-dotenv` — загрузка `.env`
- `git-filter-repo` — очистка истории git

## Использование в Python

```python
from dotenv import load_dotenv
load_dotenv()  # загружает .env автоматически

import os
token = os.environ.get("GITHUB_TOKEN")
```

## Будущее

Перейти на системный pip:
```bash
python3 -m pip install --user python-dotenv
```

Это уменьшит фрагментацию venv.
