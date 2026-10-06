#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
GRID_WIDTH = 53
GRID_HEIGHT = 7
CELL = 12
GAP = 4
PADDING = 18

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "contributions.json"
OUT_PATH = ROOT / "contrib-heatmap.svg"


def iso_to_date(value: str) -> date:
    return date.fromisoformat(value)


def build_daily_map(days: list[dict]) -> dict[str, int]:
    return {entry["date"]: int(entry["count"]) for entry in days}


def create_svg(data: dict) -> str:
    days = data.get("days", [])
    daily_map = build_daily_map(days)
    if not days:
        raise ValueError("No contribution days available to render.")

    start_date = iso_to_date(days[0]["date"])
    end_date = iso_to_date(days[-1]["date"])
    grid_start = start_date - timedelta(days=start_date.weekday() + 1)
    grid_end = end_date + timedelta(days=(6 - end_date.weekday()))

    chart_width = (GRID_WIDTH * CELL) + ((GRID_WIDTH - 1) * GAP)
    chart_height = (GRID_HEIGHT * CELL) + ((GRID_HEIGHT - 1) * GAP)
    svg_width = chart_width + (PADDING * 2)
    svg_height = 190

    cells = []
    for week_index in range(GRID_WIDTH):
        for day_index in range(GRID_HEIGHT):
            cell_date = grid_start + timedelta(weeks=week_index, days=day_index)
            count = daily_map.get(cell_date.isoformat(), 0)
            color = PALETTE[min(count, len(PALETTE) - 1)]
            x = PADDING + week_index * (CELL + GAP)
            y = PADDING + day_index * (CELL + GAP)
            delay = (week_index * 0.06) + (day_index * 0.02)
            cells.append(
                f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{color}" opacity="0.18" style="animation-delay:{delay:.2f}s;"/>'
            )

    total_contributions = data.get("total_contributions", sum(day["count"] for day in days))
    stamp = f"{total_contributions:,} contributions in the last year"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}" role="img" aria-label="GitHub contribution heatmap for Ozen-X">
  <defs>
    <style>
      .cell {{
        opacity: 0;
        transform-box: fill-box;
        transform-origin: center;
        animation: reveal 0.32s ease-out forwards;
      }}
      .label {{
        font: 12px 'Segoe UI', sans-serif;
        fill: #c9d1d9;
      }}
      .muted {{
        font: 11px 'Segoe UI', sans-serif;
        fill: #8b949e;
      }}
      @keyframes reveal {{
        0% {{ opacity: 0; transform: translate(-4px, -4px) scale(0.85); }}
        100% {{ opacity: 1; transform: translate(0, 0) scale(1); }}
      }}
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#0d1117" rx="12"/>
  <g>
    <text x="18" y="22" class="label">contributions.sh</text>
    <text x="18" y="150" class="muted">{stamp}</text>
    <g transform="translate(10, 30)">
      {''.join(cells)}
    </g>
    <g transform="translate(20, 135)">
      <text x="0" y="0" class="muted">Less</text>
      <rect x="36" y="-10" width="12" height="12" rx="2" fill="#161b22"/>
      <rect x="52" y="-10" width="12" height="12" rx="2" fill="#0e4429"/>
      <rect x="68" y="-10" width="12" height="12" rx="2" fill="#006d32"/>
      <rect x="84" y="-10" width="12" height="12" rx="2" fill="#26a641"/>
      <rect x="100" y="-10" width="12" height="12" rx="2" fill="#39d353"/>
      <rect x="116" y="-10" width="12" height="12" rx="2" fill="#69f0a0"/>
      <text x="136" y="0" class="muted">More</text>
    </g>
  </g>
</svg>
'''
    return svg


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    svg = create_svg(data)
    OUT_PATH.write_text(svg, encoding="utf-8")
    print(f"Wrote heatmap to {OUT_PATH}")


if __name__ == "__main__":
    main()
