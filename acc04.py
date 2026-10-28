# Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Job acc04 (pilot): how much shorter do MV2's Andrews-Curtis paths get with larger shortcut radii?
SAIR / Caltech Andrews-Curtis Conjecture Challenge, Discovery Track
(github.com/SAIRcompetition/Andrews-Curtis, Apache-2.0; deadline 2026-11-30). Predictions in
acc04-predictions.md, written before the job ran.

acc03 (2026-10-27, every graded check held in all four shards) solved 5,716 of the 10,115 scored
presentations, and its shortener (acc03.c with every state within 3 moves of a path state met with
every state within 3 moves of a later one, "r3/r3") cut total path length by about 31%. Only the
shortest verified path on a presentation scores, and the leaders score on about 5,500 presentations,
so length is now the lever. acc03.c also takes radius 4 on either side. Nobody has measured what that
gains on these paths, or what it costs; this pilot does, before any bulk job.

    stage s33  acc03's search and shortener, unchanged (acc03.solve, acc03.shorten_rows)
    stage s43  acc03.c --r1 4 --r2 3 on the s33 paths, then acc01's cut at the target's ball
    stage s44  acc03.c --r1 4 --r2 4 (tables up to 16,000,000 entries; longer paths fall back to
               r2 3 inside acc03.c) on the s43 paths, then the same cut
    verify     every final path, as AC (and as Stable AC for the scored set), through the
               challenge's verifier

A stage's path is kept only if it is strictly shorter and acc01's moves replay it to exactly (x, y)
within the verifier's limits. The stages share a wall-clock budget (--minutes); a path the budget
does not reach keeps its earlier path and is counted as not reached.

Two sets: "train" (the 424 training presentations, training manifest) and "scored" (the first --n
presentations of acc03's shard a, official manifest). Paths stay private until the challenge closes;
only counts are published.

Usage: python acc04.py --part pilot|grade --set train|scored [--n N] [--workers W] [--minutes M]
       [--out-dir D]
       (acc01.py, acc02.py, acc02.c, acc03.py and acc03.c of ac-discovery, and the challenge
       repository unpacked by acc01's fetch, in the working directory)
"""
import argparse
import collections
import json
import os
import subprocess
import tempfile
import time

import acc01
import acc02
import acc03

STAGES = (("s43", ["--r1", "4", "--r2", "3", "--rounds", "4"]),
          ("s44", ["--r1", "4", "--r2", "4", "--rounds", "4", "--max-entries", "16000000"]))
STAGE_NAMES = ("s33",) + tuple(s for s, _ in STAGES)


def run_short_until(jobs, workers, opts, deadline):
    """{id: parsed line} from acc03.c on {id: ((r0, r1), path)}, shortest paths first, split over
    `workers` processes; processes still running at the deadline are killed and only their complete
    lines are kept (acc03.c flushes after every line)."""
    ids = sorted(jobs, key=lambda c: (len(jobs[c][1]), c))
    parts = [ids[k::workers] for k in range(workers)]
    procs, outs = [], []
    got = {}
    with tempfile.TemporaryDirectory() as d:
        for k, part in enumerate(parts):
            if not part:
                continue
            src = os.path.join(d, f"in{k}.txt")
            with open(src, "w") as f:
                for cid in part:
                    (r0, r1), path = jobs[cid]
                    f.write(f"{cid} {acc02.to_str(r0)} {acc02.to_str(r1)} "
                            f"{','.join(map(str, path)) or '-'}\n")
            out = open(os.path.join(d, f"out{k}.txt"), "w+")
            procs.append(subprocess.Popen([acc03.SHORT] + opts, stdin=open(src), stdout=out))
            outs.append(out)
        while any(p.poll() is None for p in procs) and time.time() < deadline:
            time.sleep(2)
        for p in procs:
            if p.poll() is None:
                p.kill()
                p.wait()
        for out in outs:
            out.seek(0)
            for line in out:
                if not line.endswith("\n"):
                    continue                     # cut off by the kill
                try:
                    r = acc03.parse_short(line)
                except (IndexError, ValueError):
                    continue
                if r["status"] != "OK" or len(r["path"]) == r["new"]:
                    got[r["id"]] = r
            out.close()
    return got


def apply_stage(rows, starts, name, got, ball):
    """Record stage `name` on the rows with a path, in place; keep a strictly shorter path that
    acc01's moves replay to exactly (x, y) within the limits."""
    for r in rows:
        if "path" not in r:
            continue
        s = got.get(r["challenge_id"])
        if s is None:
            r[f"{name}_status"] = "NOT_REACHED"
        else:
            r[f"{name}_status"], r[f"{name}_seconds"] = s["status"], s["seconds"]
            if s["status"] == "OK":
                new = acc01.shorten(starts[r["challenge_id"]], s["path"], ball)
                final, work, ok = acc01.replay(starts[r["challenge_id"]], new)
                if final != acc01.TARGET or not ok:
                    r[f"{name}_status"] = "BAD_REPLAY"
                elif len(new) < r["length"]:
                    r.update({"path": new, "length": len(new), "work": work, "replay_ok": True})
        r[f"{name}_length"] = r["length"]


def items_of(which, n):
    if which == "train":
        return acc01.read_jsonl(acc01.repo_path("competition", "examples", "ac.jsonl"))
    return acc02.shard_items("a")[:n]


def manifest_of(which):
    return acc01.TRAIN_MANIFEST if which == "train" else acc01.OFFICIAL_MANIFEST


def run_pilot(args):
    t0 = time.time()
    deadline = t0 + args.minutes * 60
    ok, tail = acc03.build()
    info = {"build_selftest": ok, "build_tail": tail}
    if not ok:
        acc01.save(args.out_dir, f"acc04_{args.set}_pilot.json", info)
        print(f"SUMMARY pilot {args.set} build failed", flush=True)
        return
    items = items_of(args.set, args.n)
    rows = acc03.solve(items, args, acc01.BALL)
    starts = acc03.starts_of(items, rows)
    acc03.shorten_rows(rows, starts, args.workers, acc01.BALL)
    for r in rows:
        if "path" in r:
            r["s33_length"] = r["length"]
    info["seconds"] = {"s33": round(time.time() - t0)}
    for name, opts in STAGES:
        t1 = time.time()
        jobs = {r["challenge_id"]: (starts[r["challenge_id"]], r["path"])
                for r in rows if "path" in r}
        got = run_short_until(jobs, args.workers, opts, deadline)
        apply_stage(rows, starts, name, got, acc01.BALL)
        info["seconds"][name] = round(time.time() - t1)
        print(f"stage {name}: {len(got)} of {len(jobs)} paths reached, {round(time.time() - t1)} s",
              flush=True)
    acc01.save(args.out_dir, f"acc04_{args.set}_rows.json", rows)
    got, files = acc01.verify_lines(acc01.submission_lines(rows), manifest_of(args.set),
                                    args.out_dir, f"acc04_{args.set}_sub")
    acc01.save(args.out_dir, f"acc04_{args.set}_verify.json", {"results": got, "files": files})
    info.update({"items": len(items), "files": [{k: f[k] for k in ("file", "lines", "rc")}
                                                for f in files]})
    acc01.save(args.out_dir, f"acc04_{args.set}_pilot.json", info)
    solved = sum("path" in r for r in rows)
    print(f"SUMMARY pilot {args.set} items {len(items)} solved {solved} "
          f"seconds {json.dumps(info['seconds'], sort_keys=True)}", flush=True)


def stage_stats(found, name, prev):
    xs = [r[f"{name}_length"] for r in found if f"{name}_length" in r]
    st = acc03.length_stats(xs)
    if name != "s33":
        secs = sorted(r[f"{name}_seconds"] for r in found if f"{name}_seconds" in r)
        st.update({
            "status": dict(collections.Counter(r.get(f"{name}_status") for r in found)),
            "shorter_than_prev": sum(r[f"{name}_length"] < r[f"{prev}_length"] for r in found
                                     if f"{name}_length" in r and f"{prev}_length" in r),
            "seconds_mean": round(sum(secs) / len(secs), 2) if secs else None,
            "seconds_max": secs[-1] if secs else None})
    return st


def grade(args):
    g, out = {}, {}
    info = acc01.load(args.out_dir, f"acc04_{args.set}_pilot.json")
    rows = acc01.load(args.out_dir, f"acc04_{args.set}_rows.json")
    ver = acc01.load(args.out_dir, f"acc04_{args.set}_verify.json")
    g["pilot_ran"] = info is not None and rows is not None and ver is not None
    g["build_selftest"] = bool(info and info.get("build_selftest"))
    rows, res = rows or [], (ver or {}).get("results", {})
    want = 424 if args.set == "train" else args.n
    g["items"] = len(rows) == want
    g["no_parse_error"] = not any(r["status"] == "PARSE_ERROR" for r in rows)
    g["no_error"] = not any(acc03.has_error(r) for r in rows)
    found = [r for r in rows if "path" in r]
    g["replay_ok"] = all(r["replay_ok"] for r in found)
    g["ac_verified"] = all(res.get(r["challenge_id"], [False])[0] for r in found)
    if args.set == "scored":
        g["sac_verified"] = all(res.get("s" + r["challenge_id"], [False])[0] for r in found)
    g["lengths_agree"] = all(res.get(r["challenge_id"], [0, -1])[1] == r["length"] for r in found)
    g["never_longer"] = all(r["length"] <= r.get("s44_length", r["length"])
                            <= r.get("s43_length", r["length"]) <= r["s33_length"]
                            <= r["orig_length"] for r in found)
    g["no_stage_error"] = not any(r.get(f"{s}_status") in ("ERROR", "BAD_REPLAY")
                                  for r in found for s, _ in STAGES)
    out.update({"solved": len(found), "of": len(rows),
                "orig_lengths": acc03.length_stats([r["orig_length"] for r in found]),
                "stages": {s: stage_stats(found, s, p)
                           for s, p in zip(STAGE_NAMES, ("",) + STAGE_NAMES)},
                "stage_seconds": (info or {}).get("seconds")})
    out["graded"] = g
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["pilot", "grade"], default="pilot")
    ap.add_argument("--set", choices=["train", "scored"], default="train")
    ap.add_argument("--n", type=int, default=240)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--minutes", type=float, default=120.0)
    ap.add_argument("--a-seconds", type=float, default=1.5)
    ap.add_argument("--b-seconds", type=float, default=4.0)
    ap.add_argument("--c-seconds", type=float, default=10.0)
    ap.add_argument("--nodes", type=int, default=1500000)
    ap.add_argument("--c-nodes", type=int, default=3000000)
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    if args.part == "pilot":
        acc01.BALL.update(acc01.build_ball(5))
        run_pilot(args)
    else:
        out = grade(args)
        acc01.save(args.out_dir, f"acc04_{args.set}_grade.json", out)
        bad = sorted(k for k, v in out["graded"].items() if not v)
        extra = {k: v for k, v in out.items() if k != "graded"}
        print(f"SUMMARY grade {args.set} all_match {not bad} graded {len(out['graded'])} "
              f"failed {bad} {json.dumps(extra, sort_keys=True)}", flush=True)


if __name__ == "__main__":
    main()
