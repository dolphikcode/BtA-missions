# BtA mission content — formatVersion 3

Missions are single-language image-reveal maps. There is no story content:
each mission is a tile grid laid over a hidden image, and the player uncovers
tiles by spending points or solving in-app quiz games.

## index.json

```json
{
  "formatVersion": 3,
  "lastUpdate": "2026-10-19 20:48",
  "exercises": ["exercises.json"],
  "missions": ["mission_1.json"]
}
```

- `missions` is a **flat list of file names** — no language map. The app bumps
  its stored `content_marker` when `lastUpdate` changes.
- The app only imports when `formatVersion == 3`.

## mission_X.json

```json
{
  "id": "20b83795-81ac-438b-8322-144a2a67ab0a",
  "title": "First Recon",
  "description": "Your first field assignment. ...",
  "image": "images/mission_1.jpg",
  "coverImage": "images/badge_mission1.png",
  "sortOrder": 1,
  "gridColumns": 10,
  "gridRows": 10,
  "optimalDays": 14,
  "deadlineDays": 60,
  "rewardXp": 300,
  "rewardHealth": 0.05,
  "rewardKnowledge": 50,
  "rewardCash": 100,
  "tiles": [
    { "id": "mission1-r0c0", "col": 0, "row": 0, "type": "knowledge", "cost": 11.8 },
    { "id": "mission1-r9c0", "col": 0, "row": 9, "type": "strength", "isEntry": true, "cost": 11.26 },
    { "id": "mission1-r9c9", "col": 9, "row": 9, "type": "quiz" }
  ]
}
```

### Mission fields

| field | meaning |
|---|---|
| `id` | UUID, stable forever — player progress references it |
| `title` / `description` | shown on the mission hub card |
| `image` | hidden 1024x1024 image under `images/`, revealed tile-by-tile |
| `coverImage` | optional cover art (also under `images/`) |
| `sortOrder` | unlock order — mission N unlocks at 80% progress of mission N-1 |
| `gridColumns` / `gridRows` | tile grid size (10x10 by default) |
| `optimalDays` | target completion time (informational) |
| `deadlineDays` | mission expires this many days after activation |
| `rewardXp` / `rewardHealth` / `rewardKnowledge` / `rewardCash` | granted once at 100% completion |

### Tile fields

| field | meaning |
|---|---|
| `id` | unique within the file; player tile state references it |
| `col` / `row` | grid position, 0-based; row 0 is the TOP of the image |
| `type` | `cardio`, `strength`, `knowledge` or `quiz` |
| `isEntry` | exactly one tile: the lower-left corner `(0, gridRows-1)`. It is the only tile revealable before anything is uncovered — it still costs points / requires a quiz |
| `cost` | point cost for cost tiles; **knowledge is in displayed units** (the app stores centi-units). Omit on quiz tiles |

Rules enforced by `validate_missions.py`: tiles fill the whole grid,
`(col,row)` unique and in bounds, exactly one `isEntry` at the lower-left
corner, valid types, positive `cost` on cost tiles.

## Reveal rules (app side)

- The entry tile is the only tile available on a fresh map. Revealing a tile
  makes its four orthogonal neighbours available, and so on.
- Cost tiles deduct the price via the point ledger; quiz tiles reveal for free
  once the assigned mini-game is solved.
- Quizzes are **not** described in the JSON. The app keeps a local `quizzes`
  registry table (flashcard quiz, math quiz, ...) and assigns a random enabled
  quiz to each quiz tile on first attempt.

## Generating a mission

```bash
python generate_mission.py --title "First Recon" --image images/mission_1.jpg \
    --out mission_1.json

# custom cost ranges (MIN:MAX per type), reproducible output
python generate_mission.py --title "Deep Cover" --image images/mission_2.jpg \
    --cardio 15:40 --strength 15:40 --knowledge 8:25 \
    --reward-xp 500 --out mission_2.json --seed 42
```

Defaults: 10x10 grid, 40% quiz tiles, the remaining 60% split evenly between
cardio/strength/knowledge with costs drawn from 10:30 / 10:30 / 5:20.
Costs are rolled first, then all tiles are shuffled onto the grid.

Always run `python validate_missions.py` before pushing.
