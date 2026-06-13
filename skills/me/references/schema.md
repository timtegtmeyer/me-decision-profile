# Decision Profile — schema & dimension legend

The profile is stored as `profiles/<slug>.dpf.json`. It is **numeric-only** (plus
name, version, build date) and **language-neutral** — a profile built in German answers
questions in English or Spanish equally well. It NEVER stores question text or chosen
answers — only computed 0–100 integer scores. This keeps it tiny and token-efficient.

> Note: the **question banks** are trilingual — in `question_bank.json` /
> `stress_scenarios.json` each `q` and each option `label` is an object `{en,de,es}`. The
> scorer ignores that text entirely (it reads only `id`, option `key`, and `map`), so the
> profile schema below is unaffected by language.

`<slug>` = lowercased full name, non-alphanumerics → `-` (e.g. `Tim Niko Tegtmeyer`
→ `tim-niko-tegtmeyer`).

## Top-level

| key | meaning |
|---|---|
| `v` | schema version (currently `1`) |
| `n` | full name (the only free-text field) |
| `ts` | build date, ISO `YYYY-MM-DD` |
| `cv` | Core Values block |
| `par` | Parenting block |
| `risk` | Risk-tolerance block |
| `dec` | Decision-style block |
| `cft` | Conflict-style block |
| `pri` | Life-priorities block |
| `cfg` | meta: `conf` (confidence 0–99), `nq` (base questions answered), `ns` (stress-tests answered), `cdc` (contradiction count) |

All block values are integers 0–100. Higher = stronger pull toward that dimension.

## Core Values — `cv`
`fam` Family · `fre` Freedom · `sec` Security · `ach` Achievement · `sta` Status ·
`wlt` Wealth · `lrn` Learning · `cur` Curiosity · `ctr` Contribution · `fth` Faith ·
`com` Community

## Parenting — `par`
`ind` Independence · `dis` Discipline · `emo` Emotional resilience · `cre` Creativity ·
`acd` Academic focus · `rsk` Risk exposure · `tec` Technology tolerance ·
`soc` Social development

## Risk tolerance — `risk`  (higher = more risk-tolerant)
`fin` Financial · `car` Career · `par` Parenting · `hlt` Health

## Decision style — `dec`
`evi` Evidence · `int` Intuition · `exp` Expert authority · `con` Consensus ·
`lng` Long-term thinking

## Conflict style — `cft`
`dir` Directness · `har` Harmony · `bnd` Boundary setting · `asr` Assertiveness

## Life priorities — `pri`  (relative emphasis driving big decisions)
`car` Career-first · `fam` Family-first · `fre` Freedom-first · `pur` Purpose-first ·
`wlt` Wealth-first

## Example

```json
{"v":1,"n":"Tim Niko Tegtmeyer","ts":"2026-06-13",
 "cv":{"fam":92,"fre":88,"sec":34,"ach":71,"sta":18,"wlt":62,"lrn":95,"cur":83,"ctr":79,"fth":5,"com":53},
 "par":{"ind":94,"dis":71,"emo":90,"cre":82,"acd":56,"rsk":67,"tec":49,"soc":84},
 "risk":{"fin":73,"car":81,"par":61,"hlt":32},
 "dec":{"evi":91,"int":47,"exp":65,"con":24,"lng":93},
 "cft":{"dir":88,"har":40,"bnd":76,"asr":81},
 "pri":{"car":58,"fam":74,"fre":66,"pur":61,"wlt":29},
 "cfg":{"conf":94,"nq":64,"ns":10,"cdc":2}}
```

(`conf` 94 = `40 + 45·1 + 15·1 − 3·2`, the formula in `scoring.md` at full coverage,
all 10 stress-tests, and 2 contradictions.)
