# Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Job acc07 (second beam pilot): is time what stops acc06's widest beam? SAIR / Caltech
Andrews-Curtis Conjecture Challenge, Discovery Track (github.com/SAIRcompetition/Andrews-Curtis,
Apache-2.0; deadline 2026-11-30). Predictions in acc07-predictions.md, written before the job ran.

What acc06 found (results/acc06): on the first 240 presentations of acc05's shard a0, beams over
the verifier's own moves at widths 1k, 8k and 64k solved 86, and where they solved, the shortest
path was 34% shorter in total than acc05a0's; but acc05a0 solved 142, so the cut over all 142 was
12.6%, inside acc06's 10-25% rule. Every one of the 170 presentations w64k left unsolved stopped at
its 45 s limit, after 102 to 224 levels (median about 160), while the narrower beams mostly ran all 600 levels
without a path. So the widest beam ran out of time, not out of states.

acc07 runs acc06.c at width 64k with over five times the time (240 s, up to 600 levels) on 80
of the presentations acc06 left unsolved (acc07_items.json): the 56 that acc05a0 solved ("ref") and the
first 24 that neither solved ("unsolved"). Paths are shortened with s33 as in acc06, verified as AC
and Stable AC with the challenge's verifier and the official manifest, and those strictly shorter
than acc05a0's (or for presentations it did not solve) go into their own files, for upload.
Paths stay private until the challenge closes; only counts are published.

Usage: python acc07.py --part pilot|grade [--workers W] [--minutes M] [--out-dir D]
       (acc01.py to acc06.py, acc02.c, acc03.c and acc06.c of ac-discovery, the challenge
       repository unpacked by acc01's fetch, acc07_items.json and ref_acc05a0.json in the
       working directory)
"""
import argparse
import collections
import json
import os
import time

import acc01
import acc03
import acc04
import acc05
import acc06

CONFIG = ("w64k240", ["--width", "64000", "--max-depth", "600", "--seconds", "240"])
NAME = CONFIG[0]
ITEMS_FILE = "acc07_items.json"
GROUPS = ("ref", "unsolved")
BEAM_SHARE = 0.85               # of --minutes for the beam; the rest for s33 and the verifier


def load_items():
    """[(id, description)] in shard a0's order and {id: group}, from acc07_items.json."""
    with open(ITEMS_FILE) as f:
        want = json.load(f)
    group = {cid: g for g in GROUPS for cid in want[g]}
    return [(cid, d) for cid, d in acc05.items_of("a", 0)[:240] if cid in group], group


def run_pilot(args):
    t0 = time.time()
    deadline = t0 + args.minutes * 60
    ok, tail = acc06.build()
    info = {"build_selftest": ok, "build_tail": tail, "seconds": {}}
    if not ok:
        acc01.save(args.out_dir, "acc07_pilot.json", info)
        print(f"SUMMARY pilot build failed {tail[-600:]}", flush=True)
        return
    items, group = load_items()
    ref = acc06.load_ref()
    starts, rows = {}, []
    for cid, desc in items:
        row = {"challenge_id": cid, "group": group[cid], "ref": ref.get(cid)}
        try:
            starts[cid] = acc01.parse(desc)
            row["start_total"] = acc01.total(starts[cid])
        except ValueError as e:
            row.update({"status": "PARSE_ERROR", "reason": str(e)})
        rows.append(row)
    ids = [r["challenge_id"] for r in rows if r["challenge_id"] in starts]
    byid = {r["challenge_id"]: r for r in rows}
    t1 = time.time()
    got = acc06.run_beam(starts, ids, args.workers, CONFIG[1], t0 + args.minutes * 60 * BEAM_SHARE)
    info["seconds"][NAME] = round(time.time() - t1)
    for cid in ids:
        r, b = byid[cid], got.get(cid)
        if b is None:
            r[NAME] = {"status": "NOT_REACHED"}
            continue
        c = {"status": b["status"], "levels": b["levels"], "seconds": b["seconds"]}
        if b["status"] == "SOLVED":
            final, work, okr = acc01.replay(starts[cid], b["path"])
            if final != acc01.TARGET or not okr or len(b["path"]) != b["length"]:
                c["status"] = "BAD_REPLAY"
            else:
                c.update({"length": b["length"], "path": b["path"]})
        r[NAME] = c
    print(f"beam {NAME}: {len(got)} of {len(ids)} reached, "
          f"{sum(byid[c][NAME]['status'] == 'SOLVED' for c in ids)} solved, "
          f"{info['seconds'][NAME]} s", flush=True)
    t1 = time.time()
    jobs = {cid: (starts[cid], byid[cid][NAME]["path"]) for cid in ids if "path" in byid[cid][NAME]}
    got = acc04.run_short_until(jobs, args.workers, acc03.SHORT_OPTS, deadline)
    for cid in jobs:
        c, s = byid[cid][NAME], got.get(cid)
        c["s33_status"] = s["status"] if s else "NOT_REACHED"
        c["s33_length"] = c["length"]
        if s is None or s["status"] != "OK":
            continue
        new = acc01.shorten(starts[cid], s["path"], acc01.BALL)
        final, work, okr = acc01.replay(starts[cid], new)
        if final != acc01.TARGET or not okr:
            c["s33_status"] = "BAD_REPLAY"
        elif len(new) < c["length"]:
            c.update({"path": new, "s33_length": len(new)})
    info["seconds"]["s33"] = round(time.time() - t1)
    for r in rows:
        c = r.get(NAME, {})
        if "path" in c:
            p = c.pop("path")
            final, work, okr = acc01.replay(starts[r["challenge_id"]], p)
            r.update({"path": p, "length": len(p), "work": work,
                      "replay_ok": final == acc01.TARGET and okr})
    acc01.save(args.out_dir, "acc07_rows.json", rows)
    got, files = acc01.verify_lines(acc01.submission_lines(rows), acc01.OFFICIAL_MANIFEST,
                                    args.out_dir, "acc07_all")
    better = [r for r in rows if "path" in r and (r["ref"] is None or r["length"] < r["ref"])]
    got_b, files_b = acc01.verify_lines(acc01.submission_lines(better), acc01.OFFICIAL_MANIFEST,
                                        args.out_dir, "acc07_better_sub")
    acc01.save(args.out_dir, "acc07_verify.json", {"results": got, "files": files,
                                                   "better_results": got_b, "better_files": files_b})
    info.update({"items": len(items), "files": [{k: f[k] for k in ("file", "lines", "rc")}
                                                for f in files + files_b]})
    acc01.save(args.out_dir, "acc07_pilot.json", info)
    print(f"SUMMARY pilot items {len(items)} solved {sum('path' in r for r in rows)} better "
          f"{len(better)} seconds {json.dumps(info['seconds'], sort_keys=True)}", flush=True)


# ---------- grading ----------

def levels_stats(rows):
    """Levels reached and seconds used by the beam on the presentations it left unsolved."""
    cs = [r[NAME] for r in rows if r.get(NAME, {}).get("status") == "NONE"]
    return {"n": len(cs), "levels": acc03.length_stats([c["levels"] for c in cs]),
            "at_time_limit": sum(c["seconds"] >= 239.0 for c in cs),
            "at_max_depth": sum(c["levels"] >= 600 for c in cs)}


def grade(args):
    g, out = {}, {}
    info = acc01.load(args.out_dir, "acc07_pilot.json")
    rows = acc01.load(args.out_dir, "acc07_rows.json")
    ver = acc01.load(args.out_dir, "acc07_verify.json")
    g["pilot_ran"] = info is not None and rows is not None and ver is not None
    g["build_selftest"] = bool(info and info.get("build_selftest"))
    rows, ver = rows or [], ver or {}
    res, res_b = ver.get("results", {}), ver.get("better_results", {})
    g["items"] = len(rows) == args.n
    g["no_parse_error"] = not any(r.get("status") == "PARSE_ERROR" for r in rows)
    g["no_beam_error"] = not any(r.get(NAME, {}).get("status") in ("ERROR", "SKIP", "BAD_REPLAY")
                                 for r in rows)
    g["no_s33_error"] = not any(r.get(NAME, {}).get("s33_status") in ("ERROR", "BAD_REPLAY")
                                for r in rows)
    found = [r for r in rows if "path" in r]
    g["replay_ok"] = all(r["replay_ok"] for r in found)
    g["ac_verified"] = all(res.get(r["challenge_id"], [False])[0] for r in found)
    g["sac_verified"] = all(res.get("s" + r["challenge_id"], [False])[0] for r in found)
    g["lengths_agree"] = all(res.get(r["challenge_id"], [0, -1])[1] == r["length"] for r in found)
    better = [r for r in found if r["ref"] is None or r["length"] < r["ref"]]
    g["better_verified"] = all(res_b.get(r["challenge_id"], [False])[0]
                               and res_b.get("s" + r["challenge_id"], [False])[0] for r in better)
    g["s33_never_longer"] = all(r[NAME]["s33_length"] <= r[NAME]["length"] for r in rows
                                if "s33_length" in r.get(NAME, {}))
    by_group = {}
    for name in GROUPS:
        part = [r for r in rows if r.get("group") == name]
        both = [r for r in part if "path" in r and r["ref"] is not None]
        by_group[name] = {"items": len(part),
                          "solved": sum("path" in r for r in part),
                          "both_solved": len(both),
                          "both_sum": sum(r["length"] for r in both),
                          "both_sum_ref": sum(r["ref"] for r in both),
                          "shorter_than_ref": sum(r["length"] < r["ref"] for r in both),
                          "lengths": acc03.length_stats([r["length"] for r in part if "path" in r]),
                          "unsolved_beam": levels_stats(part)}
    out.update({
        "items": len(rows),
        "solved": len(found),
        "better": len(better),
        "groups": by_group,
        "status": dict(collections.Counter(r.get(NAME, {}).get("status", "MISSING") for r in rows)),
        "config": acc06.config_stats(rows, NAME),
        "seconds": (info or {}).get("seconds"),
        "files": (info or {}).get("files")})
    out["graded"] = g
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["pilot", "grade"], default="pilot")
    ap.add_argument("--n", type=int, default=80)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--minutes", type=float, default=240.0)
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    if args.part == "pilot":
        acc01.BALL.update(acc01.build_ball(5))
        run_pilot(args)
    else:
        out = grade(args)
        acc01.save(args.out_dir, "acc07_grade.json", out)
        bad = sorted(k for k, v in out["graded"].items() if not v)
        extra = {k: v for k, v in out.items() if k != "graded"}
        print(f"SUMMARY grade all_match {not bad} graded {len(out['graded'])} failed {bad} "
              f"{json.dumps(extra, sort_keys=True)}", flush=True)


if __name__ == "__main__":
    main()
