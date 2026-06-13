#!/usr/bin/env python3
"""
score.py — deterministic scorer for the Decision Profile skill.

Reads one or more question banks (question_bank.json, stress_scenarios.json)
plus a transient answers file (qid -> chosen option key) and writes a compact,
numeric-only profile (<slug>.dpf.json). NO answer text is ever stored — only
normalized 0-100 integer scores.

Usage (run from the skill directory, as SKILL.md does):
  python3 scripts/score.py \
      --bank references/question_bank.json \
      --bank references/stress_scenarios.json \
      --answers /tmp/answers.json \
      --name "Tim Niko Tegtmeyer" \
      [--date 2026-06-13] \
      [--out profiles/<slug>.dpf.json]

If --out is omitted it defaults to <skill_dir>/profiles/<slug>.dpf.json regardless
of the current working directory.

answers.json (base ids span cv/tr/pa/rk/de/co/pr; stress ids use st):
  { "name": "Tim Niko Tegtmeyer",
    "answers": { "cv01": "A", "tr03": "B", "pa07": "A", "rk02": "B",
                 "de01": "A", "co01": "B", "pr01": "C", "st01": "C" } }
(name in answers.json is optional if --name is given; --name wins.)

Prints a human-readable summary (incl. detected contradictions) to stdout for
the report writer. Exit non-zero on any malformed input.
"""
import argparse
import datetime
import json
import os
import re
import sys
import unicodedata

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A reasonably broad interview reaches full confidence-coverage credit here; the
# bank holds more questions than this so adaptive trimming doesn't punish confidence.
COVERAGE_TARGET = 40

# Canonical dimension structure. Output always contains every key (default 0).
DIMS = {
    "cv":   ["fam", "fre", "sec", "ach", "sta", "wlt", "lrn", "cur", "ctr", "fth", "com"],
    "par":  ["ind", "dis", "emo", "cre", "acd", "rsk", "tec", "soc"],
    "risk": ["fin", "car", "par", "hlt"],
    "dec":  ["evi", "int", "exp", "con", "lng"],
    "cft":  ["dir", "har", "bnd", "asr"],
    "pri":  ["car", "fam", "fre", "pur", "wlt"],
}
VALID_PATHS = {f"{g}.{k}" for g, ks in DIMS.items() for k in ks}

LABELS = {
    "cv.fam": "Family", "cv.fre": "Freedom", "cv.sec": "Security", "cv.ach": "Achievement",
    "cv.sta": "Status", "cv.wlt": "Wealth", "cv.lrn": "Learning", "cv.cur": "Curiosity",
    "cv.ctr": "Contribution", "cv.fth": "Faith", "cv.com": "Community",
    "par.ind": "Independence", "par.dis": "Discipline", "par.emo": "Emotional resilience",
    "par.cre": "Creativity", "par.acd": "Academic focus", "par.rsk": "Risk exposure",
    "par.tec": "Technology tolerance", "par.soc": "Social development",
    "risk.fin": "Financial risk", "risk.car": "Career risk", "risk.par": "Parenting risk",
    "risk.hlt": "Health risk",
    "dec.evi": "Evidence", "dec.int": "Intuition", "dec.exp": "Expert authority",
    "dec.con": "Consensus", "dec.lng": "Long-term thinking",
    "cft.dir": "Directness", "cft.har": "Harmony", "cft.bnd": "Boundary setting",
    "cft.asr": "Assertiveness",
    "pri.car": "Career-first", "pri.fam": "Family-first", "pri.fre": "Freedom-first",
    "pri.pur": "Purpose-first", "pri.wlt": "Wealth-first",
}


def die(msg):
    print(f"score.py: ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def slugify(name):
    # Transliterate accented Latin letters to ASCII so German/Spanish names slug
    # cleanly: "José García" -> "jose-garcia", "Tim Müller" -> "tim-muller".
    s = name.strip().lower().replace("ß", "ss")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "profile"


def round_half_up(x):
    return int(x + 0.5)


def load_questions(bank_paths):
    """Return {qid: {options: {key: [(path, w), ...]}, stress: bool}}."""
    qs = {}
    for path in bank_paths:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            die(f"cannot read bank {path}: {exc}")
        items = data.get("questions") or data.get("scenarios") or []
        if not items:
            die(f"bank {path} has no 'questions' or 'scenarios'")
        for q in items:
            # Validate shapes before access so a hand-edited or runtime-personalized
            # bank fails with a clear diagnostic instead of a raw Python traceback.
            if not isinstance(q, dict):
                die(f"non-object question in {path}: {q!r}")
            qid = q.get("id")
            if not isinstance(qid, str) or not qid:
                die(f"question without a string id in {path}")
            if qid in qs:
                die(f"duplicate question id {qid}")
            options = q.get("options")
            if not isinstance(options, list) or not options:
                die(f"{qid} has no options list")
            opts = {}
            for opt in options:
                if not isinstance(opt, dict):
                    die(f"{qid} has a non-object option: {opt!r}")
                key = opt.get("key")
                if not isinstance(key, str) or not key:
                    die(f"{qid} has an option without a string key")
                if key in opts:
                    die(f"{qid} has duplicate option key '{key}'")
                mp = opt.get("map", [])
                if not isinstance(mp, list):
                    die(f"{qid} option {key} has a non-list 'map'")
                contributions = []
                for m in mp:
                    if not isinstance(m, dict):
                        die(f"{qid} option {key} has a non-object map entry")
                    d, w = m.get("d"), m.get("w")
                    if d not in VALID_PATHS:
                        die(f"{qid} option {key} maps unknown dimension '{d}'")
                    if not isinstance(w, (int, float)) or isinstance(w, bool) or w <= 0:
                        die(f"{qid} option {key} has non-positive weight for {d}")
                    contributions.append((d, float(w)))
                opts[key] = contributions
            qs[qid] = {"options": opts, "stress": bool(q.get("stress"))}
    return qs


def score(questions, answers):
    raw = {p: 0.0 for p in VALID_PATHS}
    maxp = {p: 0.0 for p in VALID_PATHS}

    # Max possible per dimension = sum over questions of the best a single
    # option could contribute to that dimension (you pick exactly one option).
    for q in questions.values():
        best = {}
        for contributions in q["options"].values():
            per_opt = {}
            for d, w in contributions:
                per_opt[d] = per_opt.get(d, 0.0) + w
            for d, w in per_opt.items():
                best[d] = max(best.get(d, 0.0), w)
        for d, w in best.items():
            maxp[d] += w

    n_base = n_stress = 0
    unanswered_max = {p: 0.0 for p in VALID_PATHS}
    for qid, choice in answers.items():
        if qid not in questions:
            die(f"answer references unknown question '{qid}'")
        q = questions[qid]
        if choice not in q["options"]:
            die(f"answer '{choice}' is not a valid option for {qid}")
        for d, w in q["options"][choice]:
            raw[d] += w
        if q["stress"]:
            n_stress += 1
        else:
            n_base += 1

    # Only normalize against the questions that were actually answered, so a
    # partial interview still yields meaningful 0-100 scores. `support[d]` counts
    # how many answered questions could have credited d — used to flag thin /
    # unmeasured dimensions so the report writer doesn't over-read a 0 or 100.
    answered = set(answers)
    eff_max = {p: 0.0 for p in VALID_PATHS}
    support = {p: 0 for p in VALID_PATHS}
    for qid in answered:
        q = questions[qid]
        best = {}
        for contributions in q["options"].values():
            per_opt = {}
            for d, w in contributions:
                per_opt[d] = per_opt.get(d, 0.0) + w
            for d, w in per_opt.items():
                best[d] = max(best.get(d, 0.0), w)
        for d, w in best.items():
            if w > 0:
                eff_max[d] += w
                support[d] += 1

    norm = {}
    for p in VALID_PATHS:
        norm[p] = round_half_up(100.0 * raw[p] / eff_max[p]) if eff_max[p] > 0 else 0
        norm[p] = max(0, min(100, norm[p]))
    return norm, n_base, n_stress, support


def detect_contradictions(n):
    """Deterministic numeric tension checks. Returns list of human strings."""
    out = []
    risk_avg = (n["risk.fin"] + n["risk.car"] + n["risk.par"] + n["risk.hlt"]) / 4.0
    if n["cv.fre"] > 65 and risk_avg < 35:
        out.append("Values freedom highly (cv.fre {}) yet is broadly risk-averse (avg risk {:.0f}) — wants the upside of autonomy but not its volatility.".format(n["cv.fre"], risk_avg))
    if n["cv.sec"] > 65 and n["risk.car"] > 65:
        out.append("Wants security (cv.sec {}) but has a high career-risk appetite (risk.car {}) — may oscillate between bold bets and retreat.".format(n["cv.sec"], n["risk.car"]))
    if n["cv.ach"] > 65 and n["pri.fam"] > 70 and n["pri.car"] < 35:
        out.append("Strong achievement drive (cv.ach {}) but declares family-first (pri.fam {}) with low career priority (pri.car {}) — ambition and stated priority diverge.".format(n["cv.ach"], n["pri.fam"], n["pri.car"]))
    if n["par.ind"] > 70 and n["par.dis"] > 75:
        out.append("Pushes child independence (par.ind {}) and high discipline (par.dis {}) together — autonomy granted inside tight control; watch where the line really is.".format(n["par.ind"], n["par.dis"]))
    if n["cft.dir"] > 70 and n["cft.har"] > 70:
        out.append("Reads as both very direct (cft.dir {}) and very harmony-seeking (cft.har {}) — likely context-dependent; confirm which dominates under real conflict.".format(n["cft.dir"], n["cft.har"]))
    if n["dec.evi"] > 70 and n["dec.int"] > 70:
        out.append("Trusts evidence (dec.evi {}) and intuition (dec.int {}) strongly at once — probably domain-split; note which governs high-stakes calls.".format(n["dec.evi"], n["dec.int"]))
    if n["cv.fth"] > 60 and n["dec.evi"] > 75:
        out.append("Strong faith (cv.fth {}) alongside strong evidence-orientation (dec.evi {}) — reconcilable, but flag when a recommendation pits them against each other.".format(n["cv.fth"], n["dec.evi"]))
    return out


def confidence(n_base, n_stress, n_available_base, n_contradictions):
    # Coverage saturates at COVERAGE_TARGET (or the whole bank, if smaller) so an
    # adaptive interview that trims redundant questions still reaches high
    # confidence — it doesn't need every last item to count as well-covered.
    target = min(COVERAGE_TARGET, n_available_base) if n_available_base else 0
    cov = min(1.0, n_base / target) if target else 0.0
    stress_frac = min(1.0, n_stress / 10.0)
    raw = 40 + 45 * cov + 15 * stress_frac - 3 * n_contradictions
    return max(0, min(99, round_half_up(raw)))


def build_profile(name, norm, n_base, n_stress, n_available_base, contradictions, date_str):
    prof = {"v": 1, "n": name, "ts": date_str}
    for g, keys in DIMS.items():
        prof[g] = {k: norm[f"{g}.{k}"] for k in keys}
    prof["cfg"] = {
        "conf": confidence(n_base, n_stress, n_available_base, len(contradictions)),
        "nq": n_base,
        "ns": n_stress,
        "cdc": len(contradictions),
    }
    return prof


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", action="append", required=True, help="bank JSON (repeatable)")
    ap.add_argument("--answers", required=True)
    ap.add_argument("--name", default=None)
    ap.add_argument("--date", default=None, help="ISO date; default today")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    questions = load_questions(args.bank)
    n_available_base = sum(1 for q in questions.values() if not q["stress"])

    try:
        with open(args.answers, "r", encoding="utf-8") as fh:
            adata = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        die(f"cannot read answers {args.answers}: {exc}")
    answers = adata.get("answers", {})
    if not answers:
        die("answers file has no 'answers' object")
    name = args.name or adata.get("name")
    if not name:
        die("no name provided (--name or answers.name)")
    date_str = args.date or datetime.date.today().isoformat()

    norm, n_base, n_stress, support = score(questions, answers)
    contradictions = detect_contradictions(norm)
    profile = build_profile(name, norm, n_base, n_stress, n_available_base, contradictions, date_str)

    out_path = args.out or os.path.join(SKILL_DIR, "profiles", f"{slugify(name)}.dpf.json")
    try:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(profile, fh, separators=(",", ":"), ensure_ascii=False)
            fh.write("\n")
    except OSError as exc:
        die(f"cannot write {out_path}: {exc}")

    # Human-readable summary for the report writer (stdout, never stored in JSON).
    print(f"Wrote {out_path}")
    print(f"Name: {name}   Date: {date_str}")
    print(f"Answered: {n_base} base + {n_stress} stress   Confidence: {profile['cfg']['conf']}")
    print("\nTop dimensions:")
    ranked = sorted(VALID_PATHS, key=lambda p: norm[p], reverse=True)
    for p in ranked[:8]:
        print(f"  {norm[p]:3d}  {LABELS[p]} ({p})")
    print("Lowest dimensions:")
    for p in ranked[-6:]:
        print(f"  {norm[p]:3d}  {LABELS[p]} ({p})")
    print(f"\nContradictions detected: {len(contradictions)}")
    for c in contradictions:
        print(f"  - {c}")

    # Thin-evidence warning: a 0 or 100 on a dimension probed by <2 answered
    # questions is one or two answers, not a strong signal. Surface it so the
    # report writer (and any later advice) treats those scores cautiously.
    unmeasured = sorted(p for p in VALID_PATHS if support[p] == 0)
    thin = sorted(p for p in VALID_PATHS if support[p] == 1)
    if unmeasured:
        print("\nUnmeasured (no answered question probed these — score 0 is 'no data', not 'low'):")
        for p in unmeasured:
            print(f"  {LABELS[p]} ({p})")
    if thin:
        print("\nThin evidence (only 1 answered question — don't over-read extremes):")
        for p in thin:
            print(f"  {norm[p]:3d}  {LABELS[p]} ({p})")


if __name__ == "__main__":
    main()
