#!/usr/bin/env python3
"""Generate a BtA mission file (content formatVersion 3).

A mission is a single tile map (default 10x10) laid over a hidden image.
Tiles have no story content — each tile is either a point-cost tile
(cardio / strength / knowledge) or a quiz tile. Quizzes are not described
in the JSON; the app picks a random registered in-app quiz game at play time.

    python generate_mission.py

The next mission number X is picked automatically (highest existing
mission_N.json + 1), output goes to mission_X.json and the file is appended
to index.json (lastUpdate is bumped automatically).

The hidden image is resolved in this order:
  1. explicit --image path (must exist or be a URL),
  2. an existing images/mission_X.<jpg|png|webp> file,
  3. generated via make_image.py — --prompt, then mission_settings.json
     "imagePrompt" (a {number}/{title} template), then a built-in default.
     Needs KENERATE_API_KEY in .env; the file is saved as
     images/mission_X.<ext>.

All generation parameters live in mission_settings.json (next to this
script) — edit it to tune defaults; CLI flags override for this run only.

Tile fractions come from the "fractions" map (cardio / strength /
knowledge / quiz). They are normalized, so they don't need to sum to 1 —
e.g. 2:2:2:4 behaves like 20/20/20/40. Costs are drawn uniformly at random
from the per-type MIN:MAX ranges ("cardio": "10:30" = each cardio tile
costs a random 10-30 points). All tiles are then shuffled and assigned to
grid cells row by row. The lower-left tile (col 0, row gridRows-1) is
marked isEntry — it still has to be paid/solved like every other tile.
"""

import argparse
import json
import random
import re
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SETTINGS_FILE = ROOT / "mission_settings.json"
INDEX_FILE = ROOT / "index.json"
TILE_TYPES = ("cardio", "strength", "knowledge", "quiz")
DEFAULT_FRACTIONS = {"cardio": 0.2, "strength": 0.2, "knowledge": 0.2, "quiz": 0.4}
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
DEFAULT_IMAGE_PROMPT = (
    "isometric top-down map artwork for a covert-ops mobile game mission {number}, "
    "square image, rich detail, muted palette"
)


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


def resolve_fractions(settings: dict, args: argparse.Namespace, parser: argparse.ArgumentParser) -> dict[str, float]:
    """Normalized per-type tile fractions. Settings carry a 'fractions' map;
    a legacy flat 'quizFraction' still feeds the quiz entry; CLI overrides win."""
    merged = dict(DEFAULT_FRACTIONS)
    merged.update({k: float(v) for k, v in (settings.get("fractions") or {}).items() if k in TILE_TYPES})
    if "quizFraction" in settings and "quiz" not in (settings.get("fractions") or {}):
        merged["quiz"] = float(settings["quizFraction"])
    for kind, value in (("cardio", args.cardio_fraction), ("strength", args.strength_fraction),
                        ("knowledge", args.knowledge_fraction), ("quiz", args.quiz_fraction)):
        if value is not None:
            merged[kind] = value
    total = sum(merged.values())
    if total <= 0:
        parser.error("tile fractions must not all be zero")
    if any(v < 0 for v in merged.values()):
        parser.error("tile fractions must not be negative")
    return {k: v / total for k, v in merged.items()}


def allocate_counts(total: int, fractions: dict[str, float]) -> dict[str, int]:
    """Largest-remainder allocation so the counts always sum to `total`."""
    raw = {k: total * f for k, f in fractions.items()}
    counts = {k: int(v) for k, v in raw.items()}
    leftover = total - sum(counts.values())
    by_remainder = sorted(raw, key=lambda k: (-(raw[k] - int(raw[k])), TILE_TYPES.index(k)))
    for kind in by_remainder:
        if leftover <= 0:
            break
        counts[kind] += 1
        leftover -= 1
    return counts


def resolve_image(args: argparse.Namespace, settings: dict, number: int, parser: argparse.ArgumentParser) -> str:
    """Returns the repo-relative image path for the mission JSON.

    Precedence: explicit --image > existing images/mission_X.* > generated
    via make_image.py (--prompt → settings imagePrompt → built-in default;
    {number} and {title} placeholders are substituted).
    """
    if args.image is not None:
        if not (ROOT / args.image).is_file() and not args.image.startswith("http"):
            parser.error(f"image not found: {args.image}")
        return args.image
    for ext in IMAGE_EXTENSIONS:
        candidate = ROOT / "images" / f"mission_{number}{ext}"
        if candidate.is_file():
            return f"images/mission_{number}{ext}"
    prompt = (args.prompt or settings.get("imagePrompt") or DEFAULT_IMAGE_PROMPT)
    prompt = prompt.replace("{number}", str(number)).replace("{title}", args.title)
    # Lazy import: make_image needs requests, dotenv and KENERATE_API_KEY —
    # users who only supply --image shouldn't require any of that.
    try:
        from make_image import generate_image
    except Exception as e:
        parser.error(f"cannot import make_image.py ({e}) — drop images/mission_{number}.jpg into the repo or pass --image")
    (ROOT / "images").mkdir(exist_ok=True)
    saved = generate_image(prompt, str(ROOT / "images" / f"mission_{number}"))
    return Path(saved).resolve().relative_to(ROOT).as_posix()


def update_index(out_name: str) -> None:
    """Append the new mission file to index.json and bump lastUpdate."""
    index = json.loads(INDEX_FILE.read_text(encoding="utf-8")) if INDEX_FILE.is_file() else {
        "formatVersion": 3,
        "exercises": ["exercises.json"],
        "missions": [],
    }
    missions = index.setdefault("missions", [])
    if out_name not in missions:
        missions.append(out_name)
    index["lastUpdate"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    s = load_settings()
    number = next_mission_number()
    parser = argparse.ArgumentParser(description="Generate a BtA v3 mission JSON (image-reveal tile map).")
    parser.add_argument("--id", default=None, help="mission UUID (random when omitted)")
    parser.add_argument("--title", default=f"Mission {number}", help=f"mission title (default: Mission {number})")
    parser.add_argument("--description", default=None, help="short mission description")
    parser.add_argument("--image", default=None, help=f"hidden image path (default: existing images/mission_{number}.* or generated via make_image.py)")
    parser.add_argument("--prompt", default=None, help="image generation prompt for make_image.py (default: settings imagePrompt → built-in template)")
    parser.add_argument("--cover-image", default=None, help="optional cover image path relative to repo root")
    parser.add_argument("--out", default=f"mission_{number}.json", help=f"output file name (default: mission_{number}.json)")
    parser.add_argument("--sort-order", type=int, default=s.get("sortOrder", number), help=f"default: {s.get('sortOrder', f'mission number = {number}')}")
    parser.add_argument("--grid", default=s.get("grid"), help=f"grid size COLSxROWS (default: {s.get('grid')})")
    parser.add_argument("--cardio", type=parse_range, default=None, metavar="MIN:MAX", help=f"cardio cost range (default: {s.get('cardio')})")
    parser.add_argument("--strength", type=parse_range, default=None, metavar="MIN:MAX", help=f"strength cost range (default: {s.get('strength')})")
    parser.add_argument("--knowledge", type=parse_range, default=None, metavar="MIN:MAX", help=f"knowledge cost range in displayed units (default: {s.get('knowledge')})")
    parser.add_argument("--cardio-fraction", type=float, default=None, metavar="F", help="fraction of cardio tiles (default: settings fractions.cardio)")
    parser.add_argument("--strength-fraction", type=float, default=None, metavar="F", help="fraction of strength tiles (default: settings fractions.strength)")
    parser.add_argument("--knowledge-fraction", type=float, default=None, metavar="F", help="fraction of knowledge tiles (default: settings fractions.knowledge)")
    parser.add_argument("--quiz-fraction", type=float, default=None, metavar="F", help="fraction of quiz tiles (default: settings fractions.quiz)")
    parser.add_argument("--reward-xp", type=int, default=s.get("rewardXp"))
    parser.add_argument("--reward-health", type=float, default=s.get("rewardHealth"))
    parser.add_argument("--reward-knowledge", type=int, default=s.get("rewardKnowledge"))
    parser.add_argument("--reward-cash", type=float, default=s.get("rewardCash"))
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for reproducible output")
    args = parser.parse_args()

    image = resolve_image(args, s, number, parser)

    cardio = args.cardio or parse_range(s.get("cardio", "10:30"))
    strength = args.strength or parse_range(s.get("strength", "10:30"))
    knowledge = args.knowledge or parse_range(s.get("knowledge", "5:20"))
    fractions = resolve_fractions(s, args, parser)

    cols, _, rows = (args.grid or "10x10").lower().partition("x")
    cols, rows = int(cols), int(rows)
    if cols < 2 or rows < 2:
        parser.error("--grid must be at least 2x2")
    total = cols * rows

    counts = allocate_counts(total, fractions)

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
        "image": image,
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
    update_index(args.out)
    print(f"wrote {out_path.name} + index.json: {cols}x{rows} = {counts['cardio']} cardio, {counts['strength']} strength, {counts['knowledge']} knowledge, {counts['quiz']} quiz; image {image}; entry at (0,{rows - 1})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
