---
name: me-ask
description: >-
  Ask a "given who this person is, what should they do?" decision question using an existing
  Decision Profile, via the /me-ask command. Usage: "/me-ask <profile-name>" — e.g.
  "/me-ask Shirley Susan Salas Rada". If the profile name is missing, list the available
  profiles and ask which one to use. Loads the named .dpf.json, then answers in that person's
  voice with a recommendation, pros/cons, confidence, and the dimensions that drove it. If no
  such profile exists, point to /me-add to build one. Shares the engine of the `me` skill.
---

# /me-ask — ask a decision question as a saved profile

Thin command wrapper around the **`me`** Decision Profile engine, so you can ask a question
under a specific person's profile in one explicit step: **`/me-ask <profile-name>`**.

## Shared engine

The profiles and loader live in the sibling **`me`** skill directory (same parent folder,
typically `~/.claude/skills/me/`). Refer to it as `<me>` below.

## Step A — Resolve the profile name

The text after `/me-ask` is the **profile name**.
- **If it's empty/missing** → list the available profiles and ask which to use:
  ```bash
  ls <me>/profiles/*.dpf.json    # show each <slug> (strip path + .dpf.json)
  ```
  Present the slugs and ask the user to pick one. If there are none, tell them and suggest
  **`/me-add <name> <language>`** to build a profile first.
- **If a name is given** → compute its slug (lowercased, non-alphanumerics → `-`) and match it
  to a file in `<me>/profiles/`. If there's no exact match, fuzzy-match against the existing
  slugs and confirm the intended person before proceeding. Never invent a profile.
- The user may append the question after the name (e.g. `/me-ask Shirley ... should she take
  the job?`). If the args clearly contain both, use the leading part as the name and the
  trailing question as the decision question. Otherwise, after loading, **ask what decision
  they want help with.**

## Step B — Load the profile

```bash
python3 scripts/load_profile.py "<Full Name or slug>"          # readable view
python3 scripts/load_profile.py "<Full Name or slug>" --raw    # raw JSON
```
Run from the `<me>` dir. If loading fails because the profile doesn't exist, stop and suggest
**`/me-add`**. Do **not** answer from a profile you couldn't load.

## Step C — Answer (in the user's language)

Follow the **"Using a profile"** section of `<me>/SKILL.md`:

1. **Identify the relevant dimensions** for the question (e.g. career → `risk.car`, `pri.car`,
   `cv.ach/sec`, `dec.lng`; parenting → `par.*` + `cv.*`/`risk.par`/`pri.fam`).
2. **Recommendation** — concrete, tailored to that person's scores.
3. **Pros / Cons** — honest, both sides.
4. **Confidence** — informed by `cfg.conf` and how directly the profile speaks to the question;
   lower it for thin, weak, or contradictory dimensions, or topics the profile doesn't cover.
5. **Dimensions used** — name the scores explicitly, keeping the abbreviation
   (e.g. "Independence (par.ind) 94").
6. If a relevant **contradiction** exists in the profile, surface it and ask which side matters
   more for this decision.

Answer in the language the user is asking in; the `.dpf.json` is language-neutral, so any
profile works in any language.

## Privacy

Profiles are personal data: read them locally, never transmit or commit them anywhere.
