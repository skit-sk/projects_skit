import json
from pathlib import Path
from datetime import datetime, timedelta


class SessionsEnricher:
    def __init__(self, template_path=None):
        if template_path is None:
            template_path = Path(__file__).parent.parent / "data" / "sessions_template.json"
        with open(template_path, "r", encoding="utf-8") as f:
            self.template = json.load(f)
        self.sessions = self.template.get("sessions", [])

    def enrich_candle(self, candle: dict, enabled_ids: list[str] | None = None) -> dict:
        ts_ms = candle.get("timestamp_ms", 0)
        if not ts_ms:
            return candle
        dt = datetime.utcfromtimestamp(ts_ms / 1000)
        seconds = dt.hour * 3600 + dt.minute * 60 + dt.second

        active_sessions = []
        for s in self.sessions:
            if enabled_ids is not None and s["id"] not in enabled_ids:
                continue
            start_parts = s["utc_start"].split(":")
            end_parts = s["utc_end"].split(":")
            start_sec = int(start_parts[0]) * 3600 + int(start_parts[1]) * 60
            end_sec = int(end_parts[0]) * 3600 + int(end_parts[1]) * 60
            if start_sec <= seconds < end_sec:
                active_sessions.append(s["id"])
            elif start_sec > end_sec and (seconds >= start_sec or seconds < end_sec):
                active_sessions.append(s["id"])

        candle["sessions"] = {"active": active_sessions}
        return candle

    def enrich_all(self, candles: list[dict], enabled_ids: list[str] | None = None) -> list[dict]:
        return [self.enrich_candle(c, enabled_ids) for c in candles]

    def get_default_enabled(self) -> list[str]:
        return [s["id"] for s in self.sessions if s.get("default_enabled", False)]
