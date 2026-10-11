#!/usr/bin/env python3
"""Validate BtA-missions content files.

Run by the mission designer before pushing:

    python validate_missions.py

Checks:
  1. index.json parses, has formatVersion, lastUpdate and mission lists per language.
  2. Every listed mission file exists and parses.
  3. No duplicate IDs anywhere (missions, operations, tiles, puzzles share one
     ID namespace — the app upserts by ID, so a duplicate silently overwrites).
  4. IDs are identical across languages (a missing/extra ID means progress and
     journal rows would break or leak between missions).
  5. Tile (col,row) positions are unique per operation and inside the grid.
  6. Every tile's puzzleId resolves to a puzzle defined in the same operation,
     puzzle_required tiles always have a puzzleId, and each operation has
     exactly one is_entry tile and at least one objective tile.
  7. Referenced images exist in the repo.

Exit code 0 = clean, 1 = errors found.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUPPORTED_FORMAT_VERSION = 2

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


def mission_files(index: dict) -> dict[str, list[str]]:
    missions = index.get("missions", {})
    if isinstance(missions, list):
        return {"en": missions}
    if isinstance(missions, dict):
        return {lang: files for lang, files in missions.items()}
    err("index.json: 'missions' must be a language map or a list")
    return {}


def collect_ids(mission: dict, label: str) -> dict[str, str]:
    """id -> description of where it was found, for error messages."""
    found: dict[str, str] = {}
    seen: set[str] = set()

    def add(kind: str, obj: dict, where: str) -> None:
        i = obj.get("id")
        if not i:
            err(f"{label}: {kind} in {where} has no 'id'")
            return
        if i in seen:
            err(f"{label}: duplicate {kind} id '{i}' (second occurrence in {where})")
        seen.add(i)
        if i in found:
            err(f"{label}: id '{i}' reused as {kind} in {where}, already a {found[i]}")
        found[i] = kind

    add("mission", mission, mission.get("title", "?"))
    for op in mission.get("operations", []):
        where = f"operation '{op.get('id', '?')}'"
        add("operation", op, where)
        positions: set[tuple] = set()
        entry_tiles = 0
        puzzle_ids = {p.get("id") for p in op.get("puzzles", [])}
        for puzzle in op.get("puzzles", []):
            add("puzzle", puzzle, where)
        for tile in op.get("tiles", []):
            add("tile", tile, where)
            pos = (tile.get("col"), tile.get("row"))
            if pos in positions:
                err(f"{label}: duplicate tile position {pos} in {where}")
            positions.add(pos)
            cols, rows = op.get("gridColumns", 6), op.get("gridRows", 8)
            if not (0 <= (pos[0] or -1) < cols and 0 <= (pos[1] or -1) < rows):
                err(f"{label}: tile '{tile.get('id')}' at {pos} outside grid {cols}x{rows} in {where}")
            if tile.get("isEntry"):
                entry_tiles += 1
            pid = tile.get("puzzleId")
            if pid and pid not in puzzle_ids:
                err(f"{label}: tile '{tile.get('id')}' references missing puzzle '{pid}' in {where}")
            if tile.get("puzzleRequired") and not pid:
                err(f"{label}: tile '{tile.get('id')}' has puzzleRequired but no puzzleId in {where}")
        if entry_tiles != 1:
            err(f"{label}: {where} has {entry_tiles} isEntry tiles (expected exactly 1)")
        if not any(t.get("type") == "objective" for t in op.get("tiles", [])):
            err(f"{label}: {where} has no objective tile")
    return found


def main() -> int:
    index = load_json(ROOT / "index.json", "index")
    if index is None:
        return 1
    if index.get("formatVersion") != SUPPORTED_FORMAT_VERSION:
        err(f"index.json: formatVersion is {index.get('formatVersion')}, expected {SUPPORTED_FORMAT_VERSION}")
    if not index.get("lastUpdate"):
        err("index.json: missing 'lastUpdate' marker")

    files_by_lang = mission_files(index)
    if not files_by_lang:
        err("index.json: no mission files listed")

    # Load exercises too — exercise ids share the exercise namespace only.
    exercise_ids: set[str] = set()
    for ex_file in index.get("exercises", []):
        data = load_json(ROOT / ex_file, f"exercises ({ex_file})")
        for ex in (data or {}).get("exercises", []):
            if ex.get("id") in exercise_ids:
                err(f"exercises: duplicate exercise id '{ex.get('id')}'")
            exercise_ids.add(ex.get("id"))

    # ids per language: language -> mission_id -> set of all ids in that file
    per_lang: dict[str, dict[str, set[str]]] = {}
    for lang, files in files_by_lang.items():
        per_lang[lang] = {}
        for filename in files:
            data = load_json(ROOT / filename, f"{lang}/{filename}")
            if data is None:
                continue
            ids = collect_ids(data, f"{lang}/{filename}")
            mission_id = data.get("id")
            if mission_id in per_lang[lang]:
                err(f"{lang}: duplicate mission id '{mission_id}' in {filename}")
            per_lang[lang][mission_id] = set(ids)

            for img in (data.get("images") or []) + ([data["coverImage"]] if data.get("coverImage") else []):
                if not (ROOT / img).is_file():
                    warn(f"{lang}/{filename}: image '{img}' not found in repo")
            for op in data.get("operations", []):
                for tile in op.get("tiles", []):
                    if tile.get("contentImage") and not (ROOT / tile["contentImage"]).is_file():
                        warn(f"{lang}/{filename}: tile image '{tile['contentImage']}' not found")

    # Cross-language ID parity — every mission must exist with the same full ID set.
    langs = sorted(per_lang)
    base = langs[0] if langs else None
    if base:
        all_mission_ids = set(per_lang[base])
        for lang in langs[1:]:
            all_mission_ids |= set(per_lang[lang])
        for mission_id in sorted(all_mission_ids):
            base_ids = per_lang[base].get(mission_id)
            if base_ids is None:
                err(f"mission '{mission_id}' missing in '{base}' files")
                continue
            for lang in langs[1:]:
                other = per_lang[lang].get(mission_id)
                if other is None:
                    err(f"mission '{mission_id}' present in '{base}' but missing in '{lang}'")
                    continue
                missing = base_ids - other
                extra = other - base_ids
                if missing:
                    err(f"mission '{mission_id}': ids in '{base}' missing from '{lang}': {sorted(missing)}")
                if extra:
                    err(f"mission '{mission_id}': ids in '{lang}' missing from '{base}': {sorted(extra)}")

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"OK — {sum(len(m) for m in per_lang.values())} mission file(s) valid across {len(files_by_lang)} language(s)"
          + (f", {len(warnings)} warning(s)" if warnings else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
