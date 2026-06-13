#!/usr/bin/env python3
"""
load_profile.py — the loadDecisionProfile() helper for the Decision Profile skill.

Loads a compact <slug>.dpf.json, validates it, and (optionally) expands the
abbreviated keys into human/AI-readable names so a model can cite scores when
answering "given who I am, what should I do?".

As a library:
    from load_profile import load_decision_profile, expand
    prof = load_decision_profile("Tim Niko Tegtmeyer")   # name or slug
    big  = expand(prof)                                   # {"Core Values": {"Family": 92, ...}, ...}

As a CLI:
    python3 load_profile.py                       # list available profiles
    python3 load_profile.py "Tim Niko Tegtmeyer"  # pretty-print expanded profile
    python3 load_profile.py tim-niko-tegtmeyer --raw
"""
import argparse
import json
import os
import re
import sys
import unicodedata

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PROFILE_DIR = os.path.join(SKILL_DIR, "profiles")

GROUPS = {
    "cv": "Core Values", "par": "Parenting", "risk": "Risk Tolerance",
    "dec": "Decision Style", "cft": "Conflict Style", "pri": "Life Priorities",
}
LABELS = {
    "cv": {"fam": "Family", "fre": "Freedom", "sec": "Security", "ach": "Achievement",
           "sta": "Status", "wlt": "Wealth", "lrn": "Learning", "cur": "Curiosity",
           "ctr": "Contribution", "fth": "Faith", "com": "Community"},
    "par": {"ind": "Independence", "dis": "Discipline", "emo": "Emotional resilience",
            "cre": "Creativity", "acd": "Academic focus", "rsk": "Risk exposure",
            "tec": "Technology tolerance", "soc": "Social development"},
    "risk": {"fin": "Financial", "car": "Career", "par": "Parenting", "hlt": "Health"},
    "dec": {"evi": "Evidence", "int": "Intuition", "exp": "Expert authority",
            "con": "Consensus", "lng": "Long-term thinking"},
    "cft": {"dir": "Directness", "har": "Harmony", "bnd": "Boundary setting",
            "asr": "Assertiveness"},
    "pri": {"car": "Career-first", "fam": "Family-first", "fre": "Freedom-first",
            "pur": "Purpose-first", "wlt": "Wealth-first"},
}


def slugify(name):
    # Must match score.py.slugify exactly so name -> slug resolution works.
    s = name.strip().lower().replace("ß", "ss")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "profile"


def _resolve(name_or_slug, profile_dir):
    slug = name_or_slug
    if name_or_slug.endswith(".dpf.json") and os.path.isfile(name_or_slug):
        return name_or_slug
    cand = os.path.join(profile_dir, f"{name_or_slug}.dpf.json")
    if os.path.isfile(cand):
        return cand
    slug = slugify(name_or_slug)
    cand = os.path.join(profile_dir, f"{slug}.dpf.json")
    if os.path.isfile(cand):
        return cand
    return None


def load_decision_profile(name_or_slug, profile_dir=None):
    """Load and validate a decision profile. Returns the compact dict.

    Raises FileNotFoundError if missing, ValueError if malformed/unsupported.
    """
    profile_dir = profile_dir or DEFAULT_PROFILE_DIR
    path = _resolve(name_or_slug, profile_dir)
    if not path:
        raise FileNotFoundError(
            f"No profile for '{name_or_slug}' in {profile_dir}. "
            f"Run /me to create one."
        )
    with open(path, "r", encoding="utf-8") as fh:
        prof = json.load(fh)
    if prof.get("v") != 1:
        raise ValueError(f"unsupported profile version: {prof.get('v')}")
    for g in GROUPS:
        if g not in prof:
            raise ValueError(f"profile missing group '{g}'")
        # Enforce the integer-only, 0-100 invariant so advice can never be built on
        # a corrupted or hand-edited profile (floats, out-of-range, non-numeric).
        for k, v in prof[g].items():
            if isinstance(v, bool) or not isinstance(v, int) or not (0 <= v <= 100):
                raise ValueError(f"{g}.{k} is not an integer in 0-100: {v!r}")
    prof["_path"] = path
    return prof


def expand(prof):
    """Expand abbreviated keys to readable names: {Group: {Name: score}}."""
    out = {}
    for g, gname in GROUPS.items():
        out[gname] = {LABELS[g].get(k, k): v for k, v in prof.get(g, {}).items()}
    return out


def top_dimensions(prof, n=8, lowest=False):
    flat = []
    for g in GROUPS:
        for k, v in prof.get(g, {}).items():
            flat.append((f"{GROUPS[g]} · {LABELS[g].get(k, k)}", f"{g}.{k}", v))
    flat.sort(key=lambda t: t[2], reverse=not lowest)
    return flat[:n]


def list_profiles(profile_dir=None):
    profile_dir = profile_dir or DEFAULT_PROFILE_DIR
    if not os.path.isdir(profile_dir):
        return []
    return sorted(f[:-len(".dpf.json")] for f in os.listdir(profile_dir)
                  if f.endswith(".dpf.json"))


def _pretty(prof):
    print(f"Decision Profile — {prof['n']}  (built {prof.get('ts', '?')})")
    cfg = prof.get("cfg", {})
    print(f"Confidence: {cfg.get('conf', '?')}   "
          f"({cfg.get('nq', '?')} questions + {cfg.get('ns', 0)} stress-tests, "
          f"{cfg.get('cdc', 0)} contradictions)\n")
    for g, gname in GROUPS.items():
        print(gname)
        for k, v in prof.get(g, {}).items():
            bar = "█" * (v // 5)
            print(f"  {v:3d} {bar:<20} {LABELS[g].get(k, k)}")
        print()
    print("Strongest signals:")
    for label, path, v in top_dimensions(prof, 6):
        print(f"  {v:3d}  {label}  [{path}]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", nargs="?", help="profile name or slug")
    ap.add_argument("--raw", action="store_true", help="print raw JSON")
    ap.add_argument("--dir", default=None, help="profiles directory override")
    args = ap.parse_args()

    if not args.name:
        profs = list_profiles(args.dir)
        if not profs:
            print("No profiles yet. Run /me to create one.")
        else:
            print("Available profiles:")
            for p in profs:
                print(f"  {p}")
        return

    try:
        prof = load_decision_profile(args.name, args.dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    if args.raw:
        clean = {k: v for k, v in prof.items() if k != "_path"}
        print(json.dumps(clean, indent=2, ensure_ascii=False))
    else:
        _pretty(prof)


if __name__ == "__main__":
    main()
