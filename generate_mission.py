#!/usr/bin/env python3
"""Generate a BtA mission file (content formatVersion 3).

A mission is a single tile map (default 10x10) laid over a hidden image.
Tiles have no story content — each tile is either a point-cost tile
(cardio / strength / knowledge) or a quiz tile. Quizzes are not described
in the JSON; the app picks a random registered in-app quiz game at play time.

Just drop images/mission_X.jpg into the repo and run:

    python generate_mission.py

The next mission number X is picked automatically (highest existing
mission_N.json + 1), the image defaults to images/mission_X.jpg and the
output to mission_X.json. Title defaults to "Mission X".

All generation parameters live in mission_settings.json (next to this
script) — edit it to tune defaults; CLI flags override for this run only.

Default distribution per 100 tiles: 20% cardio, 20% strength,
20% knowledge, 40% quiz. Costs are drawn uniformly at random from the
given per-type ranges, then ALL tiles are shuffled and assigned to grid
cells row by row. The lower-left tile (col 0, row gridRows-1) is marked
isEntry — it still has to be paid/solved like every other tile.
"""

import argparse
import json
import random
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SETTINGS_FILE = ROOT / "mission_settings.json"


def load_settings() -> dict:
    if not SETTINGS_FILE.is_file():
        return {}
    return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))


def next_mission_number() -> int:
    numbers = [int(m.group(1)) for f in ROOT.glob("mission_*.json") if (m := re.fullmatch(r"mission_(\d+)", f.stem))]
    return max(numbers, default=0) + 1


def parse_range(value: str) -> tuple[float, float]:
    lo, _, hi = value.partition(":")
    lo_f, hi_f = float(lo), float(hi)
    if lo_f <= 0 or hi_f < lo_f:
        raise argparse.ArgumentTypeError(f"invalid range '{value}' — expected MIN:MAX with 0 < MIN <= MAX")
    return lo_f, hi_f


def clean_number(value: float) -> float | int:
    return int(value) if value == int(value) else round(value, 2)


def main() -> int:
    s = load_settings()
    number = next_mission_number()
    parser = argparse.ArgumentParser(description="Generate a BtA v3 mission JSON (image-reveal tile map).")
    parser.add_argument("--id", default=None, help="mission UUID (random when omitted)")
    parser.add_argument("--title", default=f"Mission {number}", help=f"mission title (default: Mission {number})")
    parser.add_argument("--description", default=None, help="short mission description")
    parser.add_argument("--image", default=f"images/mission_{number}.jpg", help=f"hidden image path (default: images/mission_{number}.jpg)")
    parser.add_argument("--cover-image", default=None, help="optional cover image path relative to repo root")
    parser.add_argument("--out", default=f"mission_{number}.json", help=f"output file name (default: mission_{number}.json)")
    parser.add_argument("--sort-order", type=int, default=s.get("sortOrder", number), help=f"default: {s.get('sortOrder', f'mission number = {number}')}")
    parser.add_argument("--grid", default=s.get("grid"), help=f"grid size COLSxROWS (default: {s.get('grid')})")
    parser.add_argument("--cardio", type=parse_range, default=None, metavar="MIN:MAX", help=f"cardio cost range (default: {s.get('cardio')})")
    parser.add_argument("--strength", type=parse_range, default=None, metavar="MIN:MAX", help=f"strength cost range (default: {s.get('strength')})")
    parser.add_argument("--knowledge", type=parse_range, default=None, metavar="MIN:MAX", help=f"knowledge cost range in displayed units (default: {s.get('knowledge')})")
    parser.add_argument("--quiz-fraction", type=float, default=s.get("quizFraction"), help=f"fraction of quiz tiles (default: {s.get('quizFraction')})")
    parser.add_argument("--reward-xp", type=int, default=s.get("rewardXp"))
    parser.add_argument("--reward-health", type=float, default=s.get("rewardHealth"))
    parser.add_argument("--reward-knowledge", type=int, default=s.get("rewardKnowledge"))
    parser.add_argument("--reward-cash", type=float, default=s.get("rewardCash"))
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for reproducible output")
    args = parser.parse_args()

    if not (ROOT / args.image).is_file() and not args.image.startswith("http"):
        parser.error(f"image not found: {args.image} — drop it into the repo or pass --image")

    cardio = args.cardio or parse_range(s.get("cardio", "10:30"))
    strength = args.strength or parse_range(s.get("strength", "10:30"))
    knowledge = args.knowledge or parse_range(s.get("knowledge", "5:20"))

    cols, _, rows = (args.grid or "10x10").lower().partition("x")
    cols, rows = int(cols), int(rows)
    if cols < 2 or rows < 2:
        parser.error("--grid must be at least 2x2")
    total = cols * rows

    quiz_count = round(total * args.quiz_fraction)
    cost_count = total - quiz_count
    per_type = cost_count // 3
    # Give any remainder tiles to knowledge so cost tiles split evenly.
    counts = {"cardio": per_type, "strength": per_type, "knowledge": cost_count - 2 * per_type, "quiz": quiz_count}

    rng = random.Random(args.seed)
    mission_id = args.id or str(uuid.uuid4())
    short = Path(args.out).stem.replace("_", "")

    tile_kinds: list[dict] = []
    for kind, low_high in (("cardio", cardio), ("strength", strength), ("knowledge", knowledge)):
        lo, hi = low_high
        for _ in range(counts[kind]):
            tile_kinds.append({"type": kind, "cost": clean_number(rng.uniform(lo, hi))})
    tile_kinds.extend({"type": "quiz"} for _ in range(counts["quiz"]))
    rng.shuffle(tile_kinds)

    entry_col, entry_row = 0, rows - 1  # lower-left corner
    tiles = []
    for row in range(rows):
        for col in range(cols):
            kind = tile_kinds.pop()
            tile = {
                "id": f"{short}-r{row}c{col}",
                "col": col,
                "row": row,
                "type": kind["type"],
            }
            if col == entry_col and row == entry_row:
                tile["isEntry"] = True
            if "cost" in kind:
                tile["cost"] = kind["cost"]
            tiles.append(tile)

    mission = {
        "id": mission_id,
        "title": args.title,
        "sortOrder": args.sort_order,
        "image": args.image,
        "gridColumns": cols,
        "gridRows": rows,
        "rewardXp": args.reward_xp,
        "rewardHealth": args.reward_health,
        "rewardKnowledge": args.reward_knowledge,
        "rewardCash": clean_number(args.reward_cash),
        "tiles": tiles,
    }
    if args.description:
        mission["description"] = args.description
    if args.cover_image:
        mission["coverImage"] = args.cover_image

    out_path = ROOT / args.out
    out_path.write_text(json.dumps(mission, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path.name}: {cols}x{rows} = {counts['cardio']} cardio, {counts['strength']} strength, {counts['knowledge']} knowledge, {counts['quiz']} quiz; entry at (0,{rows - 1})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
