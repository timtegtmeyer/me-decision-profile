---
name: me
description: >-
  Build, update, and use a person's Decision Profile (.dpf.json) — a compact, numeric model
  of their core values, parenting philosophy, risk tolerance, decision and conflict style,
  and life priorities — via a forced-tradeoff interview plus stress-test scenarios, then
  give advice aligned with who they actually are. Trigger with the /me command (optionally
  /me de, /me es, /me en to pick a language; it asks if omitted). Also use when the user
  asks to create / update / rebuild their decision profile, or asks a "given who I am, what
  should I do?" question about parenting, education, relationships, career, lifestyle,
  ethical tradeoffs, risk/reward, or long-term life planning — in English, German
  ("Was soll ich tun?", "Entscheidungsprofil"), or Spanish ("¿Qué debería hacer?",
  "perfil de decisión"). NOT a personality test (no Myers-Briggs / DISC / astrology).
---

# /me — Decision Profile

> **Command entry points.** Three triggers share this one engine:
> - **`/me-add <profile-name> <language>`** — build/update a profile (the `me-add` skill).
> - **`/me-ask <profile-name>`** — ask a decision question under a saved profile (the `me-ask` skill).
> - **`/me [lang] [question]`** — the original interactive flow (build if missing, then answer);
>   still works and is the implementation the two commands above delegate to.
>
> All question banks, scoring scripts, i18n strings, and profiles live **here** in the `me`
> skill dir; `me-add` / `me-ask` are thin wrappers that parse their argument and run the steps below.

A Decision Profile is a stable, numeric model of how a specific person weighs values and
makes choices, so future AI interactions can answer **"Given who I am, what should I do?"**
with grounded, evidence-cited recommendations — not generic advice. It is **not** a
personality diagnosis.

Works in **English, German, and Spanish**. The profile itself (`.dpf.json`) is
language-neutral (pure numbers), so a profile built in one language answers questions in any.

## Files

```
profiles/<slug>.dpf.json     # compact numeric profile — for AI (language-neutral)
profiles/<slug>.report.md    # readable report — for humans (written in the chosen language)
```

`<slug>` = lowercased full name, non-alphanumerics → `-` (`Tim Niko Tegtmeyer` →
`tim-niko-tegtmeyer`). Paths are relative to this skill dir.

Load only when you reach that step:
- `references/i18n.md` — fixed UI strings (menu, prompts, report headings) in en/de/es
- `references/schema.md` — dimension legend + JSON schema
- `references/scoring.md` — how answers become scores (deterministic)
- `references/question_bank.json` — ~64 forced-tradeoff questions; each `q`/`label` is `{en,de,es}`
- `references/stress_scenarios.json` — 10 stress-test dilemmas (same trilingual shape)
- `references/report_template.md` — structure for the human report
- `scripts/score.py` — deterministic scorer (answers → `.dpf.json`)
- `scripts/load_profile.py` — `loadDecisionProfile()` helper

---

## Workflow

### Step 0 — Language (do this first)
The text after `/me` may be a language: `de`, `es`, or `en` (also accept
deutsch/german/alemán, español/spanish/spanisch, english/englisch/inglés — normalize to the
2-letter code). **If a valid language is given, use it silently.** If it's missing or
unrecognized, show the picker from `references/i18n.md` and wait:

```
🌍  Language / Sprache / Idioma?  →  en · de · es
```

From here on, **conduct the entire interaction in the chosen language** — prompts, menu,
questions, scenarios, the report, and your closing message. Use the localized `{en,de,es}`
text already in the banks and the strings in `references/i18n.md`.

### Step 1 — Ask the name
Ask the localized "full name" prompt (see `i18n.md`). Compute the slug from the full name.

### Step 2 — Check for an existing profile
Look for `profiles/<slug>.dpf.json`. If it exists, show the localized Use/Update/Rebuild
menu (`i18n.md`):

- **Use** → load it (see *Using a profile*) and proceed to what they wanted.
- **Update** → re-run only the categories they want to revisit, then re-score everything.
- **Rebuild** → ignore the old file and run the full interview.

If no profile exists, go to Step 3.

### Step 3 — Run the interview
Read `references/question_bank.json`. Say the localized expectations line (`i18n.md`), then:

1. **Present questions with the AskUserQuestion tool so the user clicks — never makes them
   type a letter.** Batch **up to 4 questions per AskUserQuestion call** to reduce clicks.
   For each: the `question` is `q[lang]`; each option is a choice whose **`label` is the
   option's `label[lang]`** (verbatim) with a short, neutral one-line `description` (don't
   editorialize — keep both arms equally respectable). Use a short localized `header`
   (≤12 chars, e.g. "Valores 1", "Crianza 2", "Escenario 3").
2. **Map the answer back to the option `key`.** AskUserQuestion returns the chosen `label`;
   match it to that option to recover `qid → key`. If the user picks "Other"/types something,
   or says skip/pass/"depende", treat it as a pass (omit that id; never invent a score).
3. **More than 4 options** (only `pr01`, the 5-way priorities anchor): split into two clicks
   — first offer 4 options plus a localized "Ninguna de estas / None of these / Keine davon";
   if chosen, present the remaining option(s) in a second AskUserQuestion.
4. **Be adaptive, stay forced-choice.** Skip questions clearly redundant with answers already
   given; rephrase a confusing one in the `description`. Never substitute low-value items.
5. **Record only the choice** — `qid → option key`. Append to a working file as you go (e.g.
   `/tmp/<slug>.kv`) so progress survives across turns. Never echo a running tally — it biases
   later answers.

### Step 4 — Stress-test scenarios (do this; it sharply improves quality)
Read `references/stress_scenarios.json`, say the localized stress intro, and present the 10
scenarios in the chosen language **via AskUserQuestion (clickable), same as Step 3** — these
have 3–4 options each, so they fit one question per call (batch up to 4 scenarios per call).
**Personalize 3–4** to facts that surfaced (kids' ages, career, relationships) — keep the same
option/`map` structure and only use valid dimension dot-paths; supply `{en,de,es}` (or at
least the active language) for any you author.

### Step 5 — Score (deterministic — let the script do it)
Write the working answers to a **temporary** file (not under `profiles/`), then run from the
skill dir:

```bash
python3 scripts/score.py \
  --bank references/question_bank.json \
  --bank references/stress_scenarios.json \
  --answers /tmp/<slug>.answers.json \
  --name "<Full Name>" \
  --out profiles/<slug>.dpf.json
```

`answers.json`: `{"name":"...","answers":{"cv01":"A","pa07":"B",...,"st01":"C"}}` (omit
passed ids). The script prints a summary (top/lowest dimensions, confidence, contradictions,
thin/unmeasured dims). **Delete the temp answers file afterward** — only computed values are
kept.

### Step 6 — Write the human report
Using the `score.py` summary + `references/report_template.md`, write
`profiles/<slug>.report.md` **in the chosen language**, using the localized section headings
and group names from `references/i18n.md`. Cite concrete scores; name contradictions
honestly; flag thin/unmeasured dimensions.

### Step 7 — Hand back
Say the localized hand-back line: strongest signals, confidence, contradictions, and offer
to answer a decision question now or refine.

---

## Using a profile — `loadDecisionProfile()`

When the user asks a "what should I do?" question (now or in a future session):

```bash
python3 scripts/load_profile.py "<Full Name>"          # readable view
python3 scripts/load_profile.py "<Full Name>" --raw    # raw JSON
```

Programmatically, `load_profile.load_decision_profile(name_or_slug)` returns the dict (and
validates it's integer-only, 0–100); `expand(prof)` gives readable group→name→score. If no
profile exists, offer to build one with `/me`.

Then answer **in the user's language**, in this shape:

1. **Load** the profile.
2. **Identify the relevant dimensions** (parenting Q → `par.*` + `cv.*`/`risk.par`/`pri.fam`;
   career Q → `risk.car`, `pri.car`, `cv.ach/sec`, `dec.lng`).
3. **Recommendation** — concrete, tailored to their scores.
4. **Pros** / **Cons** — honest, both sides.
5. **Confidence** — your own, informed by `cfg.conf` and how directly the profile speaks to
   the question. Lower it for weak, thin, or contradictory dimensions, or topics the profile
   doesn't cover.
6. **Which dimensions drove it** — name the scores explicitly (keep the abbreviation, e.g.
   "Independence (par.ind) 94"), in the user's language.

> **Recommendation:** … · **Why (from your profile):** Based on your high Independence
> (par.ind 94), high Learning (cv.lrn 95), and moderate Discipline (par.dis 71), … ·
> **Pros/Cons:** … · **Confidence:** Medium — speaks to X, thin on Y. ·
> **Dimensions used:** par.ind 94, cv.lrn 95, par.dis 71.

If a relevant **contradiction** exists, surface it: "Your profile is split — you value
Freedom (cv.fre 88) but are risk-averse (avg risk 30); which matters more here?"

---

## Principles

- **Conduct everything in the chosen language**; the `.dpf.json` stays language-neutral.
- **Forced tradeoffs only.** No agree/disagree, trait quizzes, MBTI/DISC/Enneagram/astrology.
- **Predictive value over coverage.** If an answer wouldn't change a real recommendation,
  don't ask it.
- **Determinism.** Scoring is the script's job — same answers, same profile.
- **Privacy.** Store only computed integers + name. Never persist raw answers.
- **Never feign certainty.** Recommendations are evidence-weighted, not verdicts; always say
  which scores drove them and how confident you are.
- The goal is a **stable decision model aligned with demonstrated values** — not a label.
