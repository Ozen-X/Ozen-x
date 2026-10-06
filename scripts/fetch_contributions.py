#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import date, timedelta, datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER = "Ozen-X"
URL = f"https://github.com/users/{USER}/contributions"
ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "data" / "contributions.json"


def parse_label_count(label: str) -> int:
    cleaned = label.lower()
    match = re.search(r"(\d+)\s+contribution", cleaned)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)\s+contributions", cleaned)
    if match:
        return int(match.group(1))
    return 0


def calculate_streaks(days: list[dict]) -> tuple[int, int, int, str]:
    counts = {entry["date"]: entry["count"] for entry in days}
    if not days:
        return 0, 0, 0, ""

    latest_day = max(days, key=lambda entry: entry["date"])
    cursor = date.fromisoformat(latest_day["date"])

    current = 0
    while counts.get(cursor.isoformat(), 0) > 0:
        current += 1
        cursor -= timedelta(days=1)

    longest = 0
    streak = 0
    for item in sorted(days, key=lambda x: x["date"]):
        if item["count"] > 0:
            streak += 1
            if streak > longest:
                longest = streak
        else:
            streak = 0

    best_day = max((entry["count"] for entry in days), default=0)
    best_entry = max(days, key=lambda entry: (entry["count"], entry["date"]), default={"date": "", "count": 0})
    return current, longest, best_day, best_entry["date"]


def build_monthly_totals(days: list[dict]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for entry in days:
        month_key = entry["date"][:7]
        totals[month_key] = totals.get(month_key, 0) + entry["count"]
    return dict(sorted(totals.items()))


def main() -> None:
    response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    cell_nodes = soup.select("td[data-date]") or soup.select("[data-date]")

    if not cell_nodes:
        raise RuntimeError("No contribution cells were found in the GitHub contribution calendar HTML.")

    days: list[dict] = []
    seen: set[str] = set()
    for cell in cell_nodes:
        date_value = cell.get("data-date")
        if not date_value or date_value in seen:
            continue
        level = int(cell.get("data-level") or 0)
        label = cell.get("aria-label") or ""
        count = parse_label_count(label) if label else 0
        if count == 0 and level > 0:
            count = level
        days.append({"date": date_value, "count": count, "level": level})
        seen.add(date_value)

    days.sort(key=lambda item: item["date"])
    total_contributions = sum(entry["count"] for entry in days)
    current_streak, longest_streak, best_day, best_date = calculate_streaks(days)

    payload = {
        "user": USER,
        "source_url": URL,
        "total_contributions": total_contributions,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "best_day_date": best_date,
        "monthly_totals": build_monthly_totals(days),
        "start_date": days[0]["date"],
        "end_date": days[-1]["date"],
        "days": days,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved {len(days)} contribution days to {OUT_PATH}")


if __name__ == "__main__":
    main()
