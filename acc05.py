# Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Job acc05: acc03's search on all 10,115 scored presentations of the SAIR / Caltech Andrews-Curtis
Conjecture Challenge, Discovery Track (github.com/SAIRcompetition/Andrews-Curtis, Apache-2.0;
deadline 2026-11-30), with acc04's radius-4 shortcut stages on every path, in eight shards
(predictions in acc05-predictions.md, written before the job ran).

What came back on 2026-10-28 (results/acc04): every graded check of the pilot held, and on the first
240 presentations of shard a the stages s43 (acc03.c --r1 4 --r2 3) and s44 (--r1 4 --r2 4) cut
the total length of acc03's paths by a further 12.0% (42,888 to 37,726 moves), at a mean of 4.5 s
and 6.8 s per path. acc04's decision rule for a cut of at least 8% at most 30 s per path: re-run
acc03's search in eight shards with both stages, and upload the results (on the leaderboard a later,
shorter verified path replaces the earlier one). The paths acc03 found cannot be moved into a job,
so the search runs again.

    search   acc03.solve (acc02's passes A and B, then pass C), unchanged
    s33      acc03.shorten_rows (acc03.c, r1 = r2 = 3), unchanged
    s43/s44  acc04.STAGES, through acc04.run_short_until and acc04.apply_stage, shortest paths first,
             until --minutes after the start (a path not reached keeps its earlier path)
    verify   every path, as AC and as Stable AC, through the challenge's verifier and the official
             manifest (500 lines per file)
    grade    the graded checks of acc05-predictions.md

A shard is one of acc02's shards (index mod 4) and one half of it (every second presentation of it,
from --half 0 or 1), so the eight shards a0 ... d1 take each of the 10,115 presentations once. Paths
stay private until the challenge closes; only counts are published.

Usage: python acc05.py --part run|grade --shard a..d --half 0|1 [--workers W] [--minutes M]
       [--out-dir D]
       (acc01.py, acc02.py, acc02.c, acc03.py, acc03.c and acc04.py of ac-discovery, and the
       challenge repository unpacked by acc01's fetch, in the working directory)
"""
import argparse
import collections
import json
import os
import time

import acc01
import acc02
import acc03
import acc04

HALVES = (0, 1)


def items_of(shard, half):
    """Every second presentation of acc02's shard, from position `half`."""
    return acc02.shard_items(shard)[half::2]


def tag_of(args):
    return f"acc05{args.shard}{args.half}"


def run(args):
    t0 = time.time()
    deadline = t0 + args.minutes * 60
    tag = tag_of(args)
    ok, tail = acc03.build()
    info = {"build_selftest": ok, "build_tail": tail}
    if not ok:
        acc01.save(args.out_dir, f"{tag}_run.json", info)
        print(f"SUMMARY run {tag} build failed", flush=True)
        return
    items = items_of(args.shard, args.half)
    rows = acc03.solve(items, args, acc01.BALL)
    starts = acc03.starts_of(items, rows)
    info["seconds"] = {"search": round(time.time() - t0)}
    t1 = time.time()
    acc03.shorten_rows(rows, starts, args.workers, acc01.BALL)
    for r in rows:
        if "path" in r:
            r["s33_length"] = r["length"]
    info["seconds"]["s33"] = round(time.time() - t1)
    info["reached"] = {}
    for name, opts in acc04.STAGES:
        t1 = time.time()
        jobs = {r["challenge_id"]: (starts[r["challenge_id"]], r["path"])
                for r in rows if "path" in r}
        got = acc04.run_short_until(jobs, args.workers, opts, deadline)
        acc04.apply_stage(rows, starts, name, got, acc01.BALL)
        info["seconds"][name] = round(time.time() - t1)
        info["reached"][name] = [len(got), len(jobs)]
        print(f"stage {name}: {len(got)} of {len(jobs)} paths reached, {round(time.time() - t1)} s",
              flush=True)
    acc01.save(args.out_dir, f"{tag}_rows.json", rows)
    got, files = acc01.verify_lines(acc01.submission_lines(rows), acc01.OFFICIAL_MANIFEST,
                                    args.out_dir, f"{tag}_sub")
    acc01.save(args.out_dir, f"{tag}_verify.json", {"results": got, "files": files})
    info.update({"items": len(items), "files": [{k: f[k] for k in ("file", "lines", "rc")}
                                                for f in files]})
    acc01.save(args.out_dir, f"{tag}_run.json", info)
    solved = sum("path" in r for r in rows)
    print(f"SUMMARY run {tag} items {len(items)} solved {solved} "
          f"seconds {json.dumps(info['seconds'], sort_keys=True)}", flush=True)


def grade(args):
    g, out = {}, {}
    tag = tag_of(args)
    info = acc01.load(args.out_dir, f"{tag}_run.json")
    rows = acc01.load(args.out_dir, f"{tag}_rows.json")
    ver = acc01.load(args.out_dir, f"{tag}_verify.json")
    g["run_ran"] = info is not None and rows is not None and ver is not None
    g["build_selftest"] = bool(info and info.get("build_selftest"))
    rows, res = rows or [], (ver or {}).get("results", {})
    g["shard_size"] = len(rows) == len(items_of(args.shard, args.half))
    g["no_parse_error"] = not any(r["status"] == "PARSE_ERROR" for r in rows)
    g["no_error"] = not any(acc03.has_error(r) for r in rows)
    found = [r for r in rows if "path" in r]
    g["some_solved"] = bool(found)
    g["replay_ok"] = all(r["replay_ok"] for r in found)
    g["ac_verified"] = all(res.get(r["challenge_id"], [False])[0] for r in found)
    g["sac_verified"] = all(res.get("s" + r["challenge_id"], [False])[0] for r in found)
    g["lengths_agree"] = all(res.get(r["challenge_id"], [0, -1])[1] == r["length"] for r in found)
    g["never_longer"] = all(r["length"] <= r.get("s44_length", r["length"])
                            <= r.get("s43_length", r["length"]) <= r["s33_length"]
                            <= r["orig_length"] for r in found)
    g["no_stage_error"] = not any(r.get(f"{s}_status") in ("ERROR", "BAD_REPLAY")
                                  for r in found for s, _ in acc04.STAGES)
    buckets = {}
    for r in rows:
        if "start_total" in r:
            b = buckets.setdefault(acc03.bucket(r["start_total"]), [0, 0])
            b[0] += "path" in r
            b[1] += 1
    out.update({"solved": len(found), "of": len(rows),
                "by_pass": dict(collections.Counter(r["pass"] for r in found)),
                "solved_by_bucket": buckets,
                "orig_lengths": acc03.length_stats([r["orig_length"] for r in found]),
                "stages": {s: acc04.stage_stats(found, s, p)
                           for s, p in zip(acc04.STAGE_NAMES, ("",) + acc04.STAGE_NAMES)},
                "stage_seconds": (info or {}).get("seconds"),
                "reached": (info or {}).get("reached"),
                "files": len((info or {}).get("files", []))})
    out["graded"] = g
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["run", "grade"], default="run")
    ap.add_argument("--shard", choices=list(acc02.SHARDS), default="a")
    ap.add_argument("--half", type=int, choices=HALVES, default=0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--minutes", type=float, default=240.0)
    ap.add_argument("--a-seconds", type=float, default=1.5)
    ap.add_argument("--b-seconds", type=float, default=4.0)
    ap.add_argument("--c-seconds", type=float, default=10.0)
    ap.add_argument("--nodes", type=int, default=1500000)
    ap.add_argument("--c-nodes", type=int, default=3000000)
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    if args.part == "run":
        acc01.BALL.update(acc01.build_ball(5))
        run(args)
    else:
        out = grade(args)
        acc01.save(args.out_dir, f"{tag_of(args)}_grade.json", out)
        bad = sorted(k for k, v in out["graded"].items() if not v)
        extra = {k: v for k, v in out.items() if k != "graded"}
        print(f"SUMMARY grade {tag_of(args)} all_match {not bad} graded {len(out['graded'])} "
              f"failed {bad} {json.dumps(extra, sort_keys=True)}", flush=True)


if __name__ == "__main__":
    main()
