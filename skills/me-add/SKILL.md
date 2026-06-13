---
name: me-add
description: >-
  Build (or update/rebuild) a person's Decision Profile via the /me-add command.
  Usage: "/me-add <profile-name> <language>" — e.g. "/me-add Shirley Susan Salas Rada es".
  If the profile name is missing, ask for it. If the language is missing or unrecognized,
  show the en/de/es picker and ask. Then run the full forced-tradeoff interview + stress-test
  scenarios and save a numeric .dpf.json + a human report. This is the "create/update profile"
  entry point of the Decision Profile system; the matching "ask a question as a profile" entry
  point is /me-ask. Shares the engine (question banks, scoring scripts, i18n) of the `me` skill.
---

# /me-add — build or update a Decision Profile

This is a thin command wrapper around the **`me`** Decision Profile engine. It exists so a
profile can be created in one explicit step: **`/me-add <profile-name> <language>`**.

## Shared engine

All questions, scenarios, scoring, i18n strings, and scripts live in the sibling **`me`**
skill directory (same parent folder as this one — typically
`~/.claude/skills/me/`). Refer to it as `<me>` below. Do **not** duplicate that logic here;
read and run it from `<me>`.

## Step A — Parse the arguments

The text after `/me-add` is `<profile-name> <language>`, but the name itself contains spaces
(e.g. `Shirley Susan Salas Rada es`). Resolve it like this:

1. **Language** = the *last* whitespace-separated token **iff** it is a recognized language
   (`en`/`de`/`es` or english/englisch/inglés, german/deutsch/alemán,
   spanish/spanisch/español/espanol — normalize to the 2-letter code per `<me>/references/i18n.md`).
   If the last token is a language, strip it off; the remaining text is the **profile name**.
2. If the last token is **not** a language, treat the **entire** argument string as the profile
   name and leave the language unset.
3. **If the profile name is empty/missing** → ask for it. Use the localized "full name" prompt
   from `<me>/references/i18n.md` if a language is already known; otherwise ask plainly:
   *"Whose profile should I build? Give the person's full name."*
4. **If the language is unset or unrecognized** → show the picker and wait:
   ```
   🌍  Language / Sprache / Idioma?  →  en · de · es
   ```

Compute the slug from the profile name exactly as `<me>` does: lowercased full name,
non-alphanumerics → `-` (`Shirley Susan Salas Rada` → `shirley-susan-salas-rada`).

Once both are known, **conduct the entire interaction in the chosen language.**

## Step B — Existing-profile check

Look for `<me>/profiles/<slug>.dpf.json`.
- If it **exists**, show the localized **Use / Update / Rebuild** menu (`<me>/references/i18n.md`).
  - *Use* → nothing to build; tell them it already exists and suggest **`/me-ask <name>`** to
    ask a question with it.
  - *Update* → re-run only the chosen categories, then re-score everything.
  - *Rebuild* → ignore the old file and run the full interview.
- If it does **not** exist, run the full interview.

## Step C — Run the engine (interview → score → report)

Follow **Steps 3–7 of `<me>/SKILL.md`** verbatim, in the chosen language:

1. **Interview** — present `<me>/references/question_bank.json` items with **AskUserQuestion**
   (clickable, up to 4 per call). Record only `qid → option key` to a temp file
   (e.g. `/tmp/<slug>.kv`). Never echo a running tally.
2. **Stress scenarios** — present all 10 from `<me>/references/stress_scenarios.json` via
   AskUserQuestion; personalize 3–4 to facts that surfaced.
3. **Score (deterministic)** — write a temp answers file and run, **from the `<me>` dir**:
   ```bash
   python3 scripts/score.py \
     --bank references/question_bank.json \
     --bank references/stress_scenarios.json \
     --answers /tmp/<slug>.answers.json \
     --name "<Full Name>" \
     --out profiles/<slug>.dpf.json
   ```
   Then **delete the temp answers file** — only computed integers + the name are kept.
4. **Report** — write `<me>/profiles/<slug>.report.md` in the chosen language using
   `<me>/references/report_template.md` and the headings in `<me>/references/i18n.md`.
5. **Hand back** — strongest signals, confidence, contradictions, and offer to answer a
   decision question now (which is exactly what **`/me-ask <name>`** does).

## Privacy

Persist **only** the computed numeric `.dpf.json` + the readable report. **Never** store raw
answers; delete the temp answer files. Profile files are personal data — they stay local under
`profiles/` and are never committed to any repository.
