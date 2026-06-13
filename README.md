# Decision Profile skills for Claude Code

A small set of [Claude Code](https://claude.com/claude-code) skills that build a person's
**Decision Profile** — a compact, *numeric* model of how they weigh values and make choices —
and then answer **"given who this person is, what should they do?"** with grounded,
evidence-cited recommendations instead of generic advice.

It works by running a **forced-tradeoff interview** plus **stress-test scenarios**, then
deterministically scoring the answers into a language-neutral `.dpf.json`. Works in
**English, German, and Spanish**. It is **not** a personality test (no MBTI / DISC / astrology).

> **Privacy:** the only thing ever stored is the computed integer scores + the person's name
> (`.dpf.json`) and a human-readable report (`.report.md`). Raw answers are never persisted.
> **Profiles are personal data and are never committed to this repository** — see
> [Privacy & data](#privacy--data).

## Commands

| Command | What it does |
|---|---|
| `/me-add <profile-name> <language>` | Build (or update / rebuild) a profile. Missing name → it asks; missing/invalid language → it shows the `en · de · es` picker. e.g. `/me-add Jane Q Doe es` |
| `/me-ask <profile-name>` | Ask a decision question using a saved profile. Missing name → it lists the available profiles and asks which one. e.g. `/me-ask Jane Q Doe` |
| `/me [lang] [question]` | The original all-in-one interactive flow — builds the profile if missing, then answers. The two commands above delegate to this engine. |

## Layout

```
skills/
  me/        # the engine: question banks, stress scenarios, deterministic scorer, i18n, profiles/
  me-add/    # thin command wrapper → build/update a profile
  me-ask/    # thin command wrapper → ask a question under a profile
```

`me-add` and `me-ask` carry no logic of their own; they parse their argument and run the steps
in `skills/me/SKILL.md`. All shared assets live under `skills/me/`.

## Install

Requires Python 3 (standard library only) and Claude Code.

```bash
git clone https://github.com/<your-account>/me-decision-profile.git
cd me-decision-profile
./install.sh           # copies the 3 skills into ~/.claude/skills/
```

Or copy `skills/me`, `skills/me-add`, `skills/me-ask` into `~/.claude/skills/` yourself.
Restart Claude Code, then run `/me-add <name> <language>`.

## Privacy & data

- Generated profiles live in `skills/me/profiles/` as `<slug>.dpf.json` + `<slug>.report.md`.
- Those files **stay on your machine**. `.gitignore` excludes `*.dpf.json`, `*.report.md`,
  and everything under `profiles/` except `.gitkeep`, so personal data cannot be committed.
- The scorer writes temporary answer files (e.g. `/tmp/<slug>.answers.json`) and **deletes
  them** after scoring; only the numeric profile survives.

## License

MIT — see [LICENSE](LICENSE).
