USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

REQUEST_TIMEOUT = 15
REQUEST_DELAY = 1.5  # seconds between requests to avoid blocking

SOURCES = {
    "megapteka": {
        "id": "src_001",
        "name": "Мегаптека",
        "search_url": "https://megapteka.ru/search?q={query}",
        "enabled": True,
    },
    "eapteka": {
        "id": "src_002",
        "name": "eApteka",
        "search_url": "https://eapteka.ru/search/?q={query}",
        "enabled": True,
    },
    "apteka_ru": {
        "id": "src_003",
        "name": "Apteka.ru",
        "search_url": "https://apteka.ru/search/?q={query}",
        "enabled": True,
    },
    "budzdorov": {
        "id": "src_012",
        "name": "Будь Здоров",
        "search_url": "https://saratov.budzdorov.ru/forms/{slug}",
        "enabled": True,
    },
}
