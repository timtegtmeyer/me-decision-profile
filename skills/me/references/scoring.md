# Decision Profile — scoring rules

Scoring is **deterministic** and runs in `scripts/score.py`. Claude collects answers;
the script computes the numbers. Same answers → same profile, always. This is what
makes the profile a *stable* decision model rather than a vibe.

## 1. Answers in, scores out

Each question is a forced choice. Each option carries a `map`: a list of
`{d: "<group>.<key>", w: <weight 1–3>}` contributions. When the user picks an option,
each mapped dimension gains `w` points (`raw[d] += w`).

## 2. Normalization (guarantees 0–100 integers)

For every dimension `d`, the script computes — **over the questions actually answered** —
`eff_max[d]` = the most points `d` could have earned (the best single option per question
for `d`, summed). Then:

```
score[d] = round_half_up( 100 * raw[d] / eff_max[d] )   # 0 if eff_max==0
```

Normalizing against *answered* questions (not the whole bank) means a partial interview
still yields meaningful scores. No floating-point values are ever stored — only integers.

## 3. Stress-tests weigh more

Stress scenarios use higher weights (up to `w:3`) and feed the same pass. Revealed
behavior under a concrete dilemma is stronger evidence than a stated preference, so it
moves scores more. If a stress answer contradicts the questionnaire, that surfaces as a
detected contradiction (below) and is noted in the report — trust the revealed behavior.

## 4. Contradiction detection (deterministic)

After normalization, `score.py` runs ~7 numeric tension checks (e.g. *high freedom +
broadly risk-averse*, *both very direct and very harmony-seeking*, *achievement-driven but
declares family-first with low career priority*). Each hit:
- lowers confidence (`-3` each),
- is counted in `cfg.cdc`,
- is printed for the human report's "Contradictions Detected" section.

Contradictions are not errors — they're the most decision-relevant thing in the profile.
Qualitative contradictions you notice during the interview should also go in the report.

## 5. Confidence (`cfg.conf`, 0–99)

```
conf = clamp( 40 + 45 * coverage + 15 * stress_fraction - 3 * contradictions , 0, 99 )
```

- `coverage` = base questions answered / **40** (the breadth target; capped at 1). The
  bank holds ~64 base questions, so an adaptive interview that trims redundant items to
  ~40–50 still reaches full coverage credit — you are *not* penalized for skipping
  redundant questions, which the skill explicitly encourages.
- `stress_fraction` = stress-tests answered / 10 (capped at 1).
- Never reaches 100 — the model is always provisional. Treat <60 as "thin, ask more".

`score.py` also reports **unmeasured** dimensions (no answered question probed them — a
stored 0 there means "no data", not "low") and **thin** dimensions (only 1 supporting
answer — don't over-read a 0 or 100). Reflect those caveats in the report and in advice.

## 6. What is NOT stored

The user's chosen options, the question text, any free-text elaboration. Only computed
integers + name + version + date. If you want to refine later, re-run the relevant
questions and re-score (the **Update** flow) — do not try to persist raw answers.
