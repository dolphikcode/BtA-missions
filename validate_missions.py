#!/usr/bin/env python3
"""Validate BtA-missions content files (formatVersion 3).

Run by the mission designer before pushing:

    python validate_missions.py

Checks:
  1. index.json parses, has formatVersion 3, lastUpdate, a flat 'missions'
     file list and an 'exercises' file list.
  2. Every listed file exists and parses.
  3. No duplicate IDs anywhere (missions and tiles share one ID namespace —
     the app upserts by ID, so a duplicate silently overwrites).
  4. Tiles: unique (col,row) per mission, inside the grid, exactly one
     isEntry tile at the lower-left corner (col 0, row gridRows-1), and a
     valid type — cardio/strength/knowledge tiles carry a positive 'cost',
     quiz tiles carry none.
  5. The declared tile count fills the whole grid.
  6. Referenced images exist in the repo.

Exit code 0 = clean, 1 = errors found.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUPPORTED_FORMAT_VERSION = 3
COST_TYPES = {"cardio", "strength", "knowledge"}
TILE_TYPES = COST_TYPES | {"quiz"}

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def load_json(path: Path, label: str):
    if not path.is_file():
        err(f"{label}: file not found: {path.name}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f"{label}: invalid JSON in {path.name}: {e}")
        return None


def check_image(path_value: str | None, label: str) -> None:
    if not path_value:
        return
    if path_value.startswith("http"):
        return
    if not (ROOT / path_value).is_file():
        err(f"{label}: image not found: {path_value}")


def check_mission(mission: dict, seen_ids: set[str]) -> None:
    mid = mission.get("id", "?")
    label = f"mission {mission.get('title', mid)}"
    if mid in seen_ids:
        err(f"{label}: duplicate mission id {mid}")
    seen_ids.add(mid)

    cols = mission.get("gridColumns")
    rows = mission.get("gridRows")
    if not isinstance(cols, int) or not isinstance(rows, int) or cols < 2 or rows < 2:
        err(f"{label}: missing/invalid gridColumns x gridRows")
        return

    check_image(mission.get("image"), label)
    check_image(mission.get("coverImage"), label)
    if not mission.get("image"):
        warn(f"{label}: no hidden 'image' — the map will render without a photo")

    tiles = mission.get("tiles")
    if not isinstance(tiles, list):
        err(f"{label}: 'tiles' must be a list")
        return
    if len(tiles) != cols * rows:
        err(f"{label}: {len(tiles)} tiles but grid is {cols}x{rows} = {cols * rows}")

    positions: set[tuple[int, int]] = set()
    entries: list[dict] = []
    type_counts = {"cardio": 0, "strength": 0, "knowledge": 0, "quiz": 0}
    for tile in tiles:
        tid = tile.get("id", "?")
        if tid in seen_ids:
            err(f"{label}: duplicate tile id {tid}")
        seen_ids.add(tid)
        col, row = tile.get("col"), tile.get("row")
        if not isinstance(col, int) or not isinstance(row, int):
            err(f"{label}: tile {tid} missing int col/row")
            continue
        if not (0 <= col < cols and 0 <= row < rows):
            err(f"{label}: tile {tid} at ({col},{row}) outside {cols}x{rows} grid")
        if (col, row) in positions:
            err(f"{label}: duplicate tile position ({col},{row})")
        positions.add((col, row))
        ttype = tile.get("type")
        if ttype not in TILE_TYPES:
            err(f"{label}: tile {tid} has invalid type '{ttype}'")
            continue
        type_counts[ttype] += 1
        if ttype in COST_TYPES:
            cost = tile.get("cost")
            if not isinstance(cost, (int, float)) or cost <= 0:
                err(f"{label}: {ttype} tile {tid} needs a positive 'cost'")
        elif tile.get("cost") is not None:
            warn(f"{label}: quiz tile {tid} has a 'cost' — ignored")
        if tile.get("isEntry"):
            entries.append(tile)

    if len(entries) != 1:
        err(f"{label}: expected exactly one isEntry tile, found {len(entries)}")
    elif (entries[0].get("col"), entries[0].get("row")) != (0, rows - 1):
        err(f"{label}: isEntry tile is at ({entries[0].get('col')},{entries[0].get('row')}) — must be the lower-left corner (0,{rows - 1})")

    print(f"  {label}: {cols}x{rows} - {type_counts['cardio']} cardio, {type_counts['strength']} strength, {type_counts['knowledge']} knowledge, {type_counts['quiz']} quiz")


def main() -> int:
    index = load_json(ROOT / "index.json", "index.json")
    if index is None:
        return report()

    version = index.get("formatVersion")
    if version != SUPPORTED_FORMAT_VERSION:
        err(f"index.json: formatVersion is {version}, expected {SUPPORTED_FORMAT_VERSION}")
    if not index.get("lastUpdate"):
        warn("index.json: empty lastUpdate — sync uses it as the change marker")

    mission_files = index.get("missions")
    if not isinstance(mission_files, list) or not all(isinstance(f, str) for f in mission_files):
        err("index.json: 'missions' must be a flat list of file names (v3 is single-language)")
        mission_files = []

    exercises = index.get("exercises")
    if not isinstance(exercises, list) or not all(isinstance(f, str) for f in exercises):
        err("index.json: 'exercises' must be a list of file names")
        exercises = []

    seen_ids: set[str] = set()
    for name in mission_files:
        mission = load_json(ROOT / name, "index.json")
        if mission is not None:
            check_mission(mission, seen_ids)

    for name in exercises:
        data = load_json(ROOT / name, "index.json")
        if isinstance(data, dict):
            for exercise in data.get("exercises", []):
                eid = exercise.get("id", "?")
                if eid in seen_ids:
                    err(f"exercise: duplicate id {eid}")
                seen_ids.add(eid)
                for key in ("name", "unit"):
                    if not exercise.get(key):
                        warn(f"exercise {eid}: missing '{key}'")

    return report()


def report() -> int:
    for msg in warnings:
        print(f"WARNING: {msg}")
    for msg in errors:
        print(f"ERROR: {msg}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
