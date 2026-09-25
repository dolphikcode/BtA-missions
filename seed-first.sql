-- Last update: 2026-09-24 16:54
-- BtA development seed file.
-- Executed by DevScreen → "Re-initialize" after wiping all tables and re-seeding default exercises.
-- Rules:
--   * one SQL statement per line
--   * lines starting with -- and empty lines are ignored
--   * a trailing semicolon is optional
--   * packaged into debug builds only (app/build.gradle.kts → debug assets.srcDirs)
-- Examples:
-- INSERT INTO users (id, email, nickname, passwordHash, userType, avatarPath, createdAt) VALUES ('dev-user', 'dev@bta.local', 'Dev', '<bcrypt-hash>', 'user', NULL, 1767225600000);
-- INSERT INTO users_data (id, userId, currentXp, currentHealth, currentKnowledge, currentCash) VALUES ('dev-data', 'dev-user', 0, 0.5, 0, 0);
-- INSERT INTO app_visits (userId, lastVisitedAt) VALUES ('dev-user', 1767225600000);

-- Default exercises (mirrors DefaultExercises.kt — re-initialize seeds these automatically,
-- so the statements below are only needed if you want to customize them):
INSERT OR REPLACE INTO exercises (id, name, unit, xpPerUnit, healthPerUnit, cashReward) VALUES ('d3c84ed9-de16-49a3-b7e3-444f5d982c6f', 'Walk', 'km', 10.0, 0.1, 2.0);
INSERT OR REPLACE INTO exercises (id, name, unit, xpPerUnit, healthPerUnit, cashReward) VALUES ('b396182c-534d-4e08-b508-3b2312c1d8a9', 'Pushups', 'reps', 0.1, 0.1, 0.5);
INSERT OR REPLACE INTO exercises (id, name, unit, xpPerUnit, healthPerUnit, cashReward) VALUES ('b396182c-534d-4e08-b508-3b2312c1d125', 'Squats', 'reps', 0.1, 0.1, 0.5);
INSERT OR REPLACE INTO exercises (id, name, unit, xpPerUnit, healthPerUnit, cashReward) VALUES ('b3a136f0-b8e0-4ce2-9ce8-b74c19aaa5a1', 'Daily steps', 'steps', 0.001, 0.001, 0.0001);

-- Standard task reward values per difficulty (mirrors DefaultDifficultyPresets in Models.kt)
INSERT OR REPLACE INTO difficulty_presets (difficulty, xp, knowledge, cash) VALUES ('easy', 10, 5, 5.0);
INSERT OR REPLACE INTO difficulty_presets (difficulty, xp, knowledge, cash) VALUES ('normal', 15, 8, 10.0);
INSERT OR REPLACE INTO difficulty_presets (difficulty, xp, knowledge, cash) VALUES ('hard', 30, 15, 25.0);
INSERT OR REPLACE INTO difficulty_presets (difficulty, xp, knowledge, cash) VALUES ('epic', 60, 30, 50.0);
