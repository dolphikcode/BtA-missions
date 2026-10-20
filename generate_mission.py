#!/usr/bin/env python3
"""Generate a BtA mission file (content formatVersion 3).

A mission is a single tile map (default 10x10) laid over a hidden image.
Tiles have no story content — each tile is either a point-cost tile
(cardio / strength / knowledge) or a quiz tile. Quizzes are not described
in the JSON; the app picks a random registered in-app quiz game at play time.

Default distribution per 100 tiles: 20% cardio, 20% strength,
20% knowledge, 40% quiz. Costs are drawn uniformly at random from the
given per-type ranges, then ALL tiles are shuffled and assigned to grid
cells row by row. The lower-left tile (col 0, row gridRows-1) is marked
isEntry — it still has to be paid/solved like every other tile.

Usage:

    python generate_mission.py --title "First Recon" --image images/mission_1.jpg \
        --out mission_1.json

    python generate_mission.py --title "Deep Cover" --image images/mission_2.jpg \
        --cardio 15:40 --strength 15:40 --knowledge 8:25 \
        --reward-xp 500 --out mission_2.json --seed 42
"""

import argparse
import json
import random
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def parse_range(value: str) -> tuple[float, float]:
    lo, _, hi = value.partition(":")
    lo_f, hi_f = float(lo), float(hi)
    if lo_f <= 0 or hi_f < lo_f:
        raise argparse.ArgumentTypeError(f"invalid range '{value}' — expected MIN:MAX with 0 < MIN <= MAX")
    return lo_f, hi_f


def clean_number(value: float) -> float | int:
    return int(value) if value == int(value) else round(value, 2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a BtA v3 mission JSON (image-reveal tile map).")
    parser.add_argument("--id", default=None, help="mission UUID (random when omitted)")
    parser.add_argument("--title", required=True, help="mission title")
    parser.add_argument("--description", default=None, help="short mission description")
    parser.add_argument("--image", required=True, help="hidden 1024x1024 image path relative to repo root, e.g. images/mission_1.jpg")
    parser.add_argument("--cover-image", default=None, help="optional cover image path relative to repo root")
    parser.add_argument("--out", required=True, help="output file name, e.g. mission_1.json")
    parser.add_argument("--sort-order", type=int, default=1)
    parser.add_argument("--grid", default="10x10", help="grid size COLSxROWS (default 10x10)")
    parser.add_argument("--cardio", type=parse_range, default=(10.0, 30.0), metavar="MIN:MAX", help="cardio cost range (default 10:30)")
    parser.add_argument("--strength", type=parse_range, default=(10.0, 30.0), metavar="MIN:MAX", help="strength cost range (default 10:30)")
    parser.add_argument("--knowledge", type=parse_range, default=(5.0, 20.0), metavar="MIN:MAX", help="knowledge cost range in displayed units (default 5:20)")
    parser.add_argument("--quiz-fraction", type=float, default=0.4, help="fraction of quiz tiles (default 0.4); the rest is split evenly between cardio/strength/knowledge")
    parser.add_argument("--optimal-days", type=int, default=14)
    parser.add_argument("--deadline-days", type=int, default=60)
    parser.add_argument("--reward-xp", type=int, default=300)
    parser.add_argument("--reward-health", type=float, default=0.05)
    parser.add_argument("--reward-knowledge", type=int, default=50)
    parser.add_argument("--reward-cash", type=float, default=100.0)
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for reproducible output")
    args = parser.parse_args()

    cols, _, rows = args.grid.lower().partition("x")
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
    for kind, low_high in (("cardio", args.cardio), ("strength", args.strength), ("knowledge", args.knowledge)):
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
        "optimalDays": args.optimal_days,
        "deadlineDays": args.deadline_days,
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
