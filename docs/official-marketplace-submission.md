# Submitting to the official Claude Code plugin directory

Anthropic's directory is the repo [`anthropics/claude-plugins-official`](https://github.com/anthropics/claude-plugins-official).
Third-party plugins live as **whole-repo references** (the plugin stays in *our* repo; the
directory only adds a pinned entry to its `.claude-plugin/marketplace.json`).

> **Official route:** external plugins are submitted via the
> [plugin directory submission form](https://clau.de/plugin-directory-submission), not an
> unsolicited PR. The form asks for the same fields as the JSON entry below. If a direct PR is
> invited, the entry and PR text below are ready to paste.

---

## Marketplace entry (add to the `plugins` array of `.claude-plugin/marketplace.json`)

```json
{
  "name": "me-decision-profile",
  "description": "Build a person's numeric Decision Profile via a forced-tradeoff interview + stress scenarios, then give value-aligned, evidence-cited advice. Commands: /me-add <name> <language>, /me-ask <name>, and /me. Trilingual (en/de/es). Stores only computed integers + the name; never raw answers.",
  "author": {
    "name": "Tim Niko Tegtmeyer",
    "email": "tim@timniko.com"
  },
  "source": {
    "source": "url",
    "url": "https://github.com/timtegtmeyer/me-decision-profile.git",
    "sha": "d4b3bb49805c0fa82d2376dda98e2147b2bbf142"
  },
  "category": "productivity",
  "homepage": "https://github.com/timtegtmeyer/me-decision-profile"
}
```

- `sha` pins the directory to a reviewed commit. Bump it to the new HEAD whenever a release
  should be promoted (`gh api repos/timtegtmeyer/me-decision-profile/commits/main -q .sha`).
- `category: productivity` is an existing category in the directory.

---

## PR title

```
Add me-decision-profile (external plugin)
```

## PR description

```markdown
### What
Adds **me-decision-profile**, an external (whole-repo) plugin, to the directory.

It builds a person's **Decision Profile** — a compact, numeric model of how they weigh values
and make choices — through a forced-tradeoff interview plus stress-test scenarios, then answers
"given who this person is, what should they do?" with grounded, evidence-cited recommendations.
It is **not** a personality test (no MBTI/DISC/astrology).

**Commands**
- `/me-add <name> <language>` — build or update a profile (asks for any missing argument)
- `/me-ask <name>` — ask a decision question under a saved profile
- `/me [lang] [question]` — original interactive flow

Trilingual (English / German / Spanish). Pure Python 3 standard library; no external services
and no MCP server.

### Source
- Repo: https://github.com/timtegtmeyer/me-decision-profile
- Pinned sha: `d4b3bb49805c0fa82d2376dda98e2147b2bbf142`
- License: MIT

### Privacy / security
- No network calls, no telemetry, no MCP server, no credentials.
- The only data written is a numeric `.dpf.json` + a human-readable report, stored locally.
  Raw interview answers are written to a temp file and deleted after scoring.
- No personal data ships in the repo: `.gitignore` excludes all `*.dpf.json` / `*.report.md`
  and everything under `profiles/` except `.gitkeep`.

### Checklist
- [x] `.claude-plugin/plugin.json` present and valid
- [x] Repo is also a self-contained marketplace (installable standalone)
- [x] README with install + usage
- [x] MIT licensed
- [x] No bundled secrets or personal data
```
