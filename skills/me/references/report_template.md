# Report template — `profiles/<slug>.report.md`

This report is **for humans**. The `.dpf.json` is for AI. Fill this in from the
`score.py` stdout summary plus your own read of the interview. Cite concrete scores.
Keep it honest — name the contradictions, don't flatter.

**Write the report in the interview's language.** Translate the section headings and
dimension group names using the tables in `references/i18n.md` (the structure below is the
English form). When citing a dimension, keep the abbreviation + score so it stays traceable
in any language (e.g. de "Unabhängigkeit (par.ind) 94", es "Independencia (par.ind) 94").
Reflect any **thin** or **unmeasured** dimensions that `score.py` flagged as caveats.

```markdown
# Decision Profile — {Full Name}
_Built {YYYY-MM-DD} · Confidence {conf}/99 · {nq} questions + {ns} stress-tests_

## Snapshot
2–4 sentences: the person's center of gravity. Lead with the 3–4 strongest signals
and what they mean for how this person decides. No personality-type labels.

## Core Values
Rank the top values with scores. Note the defining tradeoffs they resolved (e.g.
"Learning (95) over Wealth (62); Freedom (88) over Security (34)"). Call out anything
near the extremes (very high or very low) — those are the load-bearing values.

## Parenting Philosophy
Summarize the parenting block. Translate scores into a stance ("high Independence (94) +
high Emotional resilience (90) → raises for self-reliance and lets the child struggle
productively; moderate Academic focus (56) → won't optimize childhood for grades").

## Risk Profile
Financial / Career / Parenting / Health, with scores. Note asymmetries (e.g. bold with
career, cautious with health) — these matter more than the average.

## Decision Style
How this person should be advised: what evidence they trust, time horizon, how much to
defer to experts or the crowd. Cite `dec.*` scores.

## Conflict Style
Directness vs harmony, boundaries, assertiveness — how they handle hard conversations.

## Dominant Tradeoffs
The 4–6 tensions this profile resolves most decisively, as "X over Y (score vs score)".
This is the heart of the model — it's what lets the AI predict choices.

## Contradictions Detected
List every contradiction from `score.py` plus any you observed. For each: what pulls
which way, and how to handle it when advising (which side tends to win, or "ask").
If none: say so, and note that means the profile is internally consistent (not that it's
complete).

## Confidence & Caveats
State `conf`, what would raise it (more questions, more stress-tests, resolving
contradictions), and that recommendations built on this are provisional, not verdicts.

## How to use this profile
One line: "Future AI: load `{slug}.dpf.json`, identify relevant dimensions, and cite the
scores that drive any recommendation. Never feign certainty."
```
