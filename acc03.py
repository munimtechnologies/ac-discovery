# Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Job acc03: MV2's third pass at the 10,115 presentations of the SAIR / Caltech Andrews-Curtis
Conjecture Challenge, Discovery Track (github.com/SAIRcompetition/Andrews-Curtis, Apache-2.0;
deadline 2026-11-30): acc02's search again, a third pass on what it leaves, and acc03.c's shortener
on every path (predictions in acc03-predictions.md, written before the job ran).

acc02 (2026-10-27, every graded check held) solved 4,934 of the 10,115 (48.8%), with paths of
median length 273 to 299 by shard. Only the shortest verified path on a presentation scores (the k
teams tied for it get 2^(1-k) points each, everyone else 0), so length now matters as much as
count. acc02's searches stopped on their time caps (1.5 s and 4 s), not on their node caps.

    search    acc02's passes A and B (acc02.py, unchanged) on this shard (index mod 4, as acc02),
              then pass C on what they leave: --grow 8 --slack 32, 10 s, 3,000,000 nodes
    shorten   acc03.c on every path (every state within 3 moves of each state of the path, met
              with every state within 3 moves of a later one; rounds until nothing is gained),
              then acc01's cut at the target's ball of radius 5; the shorter path is kept only if
              acc01's moves replay it to exactly (x, y) within the verifier's limits
    verify    every path, as AC and as Stable AC, through the challenge's verifier and the official
              manifest (500 lines per file)
    grade     the graded checks of acc03-predictions.md

The control part does the same on the 424 training presentations, with the training manifest.
Paths stay private until the challenge closes; only counts are published.

Usage: python acc03.py --part build|control|search|verify|grade [--shard a..d] [--workers W]
       [--c-seconds S] [--c-nodes N] [--out-dir D]
       (acc01.py, acc02.py and acc02.c of ac-discovery, and the challenge repository unpacked by
       acc01's fetch, in the working directory)
"""
import argparse
import collections
import copy
import json
import os
import subprocess
import sys
import tempfile
import time

import acc01
import acc02

SHORT = os.path.abspath("acc03")
PASS_C = ("C", ["--grow", "8", "--slack", "32"])
SHORT_OPTS = ["--r1", "3", "--r2", "3", "--rounds", "8"]
PASS_NAMES = "ABC"


def build():
    """acc02's build and self-test, then gcc -O2 acc03.c and its self-test."""
    ok, tail = acc02.build()
    if not ok:
        return False, tail
    p = subprocess.run(["gcc", "-O2", "-o", SHORT, "acc03.c"], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    if p.returncode:
        return False, p.stdout[-2000:]
    p = subprocess.run([SHORT, "--selftest"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, timeout=900)
    return p.returncode == 0 and "SELFTEST ok" in p.stdout, tail + p.stdout[-1000:]


def parse_short(line):
    """{'id', 'status', 'old', 'new', 'rounds', 'seconds', 'path'} from a line of acc03.c."""
    f = line.split()
    path = [] if f[6] == "-" else [int(m) for m in f[6].split(",")]
    return {"id": f[0], "status": f[1], "old": int(f[2]), "new": int(f[3]), "rounds": int(f[4]),
            "seconds": float(f[5]), "path": path}


def run_short(jobs, workers, opts=SHORT_OPTS):
    """{id: parsed line} from acc03.c on {id: ((r0, r1), path)}, split over `workers` processes."""
    ids = sorted(jobs)
    parts = [ids[k::workers] for k in range(workers)]
    procs, outs = [], []
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
            procs.append(subprocess.Popen([SHORT] + opts, stdin=open(src), stdout=out))
            outs.append(out)
        for p in procs:
            p.wait()
        got = {}
        for out in outs:
            out.seek(0)
            for line in out:
                if line.strip():
                    r = parse_short(line)
                    got[r["id"]] = r
            out.close()
    return got


def starts_of(items, rows):
    """{id: (r0, r1)} for the rows with a path."""
    have = {r["challenge_id"] for r in rows if "path" in r}
    return {cid: acc01.parse(desc) for cid, desc in items if cid in have}


def shorten_rows(rows, starts, workers, ball):
    """Shorten every path in rows, in place: acc03.c, then acc01's cut at the ball. The shorter
    path is kept only if acc01's moves replay it to exactly (x, y) within the limits."""
    found = {r["challenge_id"]: r for r in rows if "path" in r}
    got = run_short({cid: (starts[cid], r["path"]) for cid, r in found.items()}, workers)
    for cid, r in found.items():
        s = got.get(cid)
        r["orig_length"] = r["length"]
        r["short_status"] = s["status"] if s else "NO_OUTPUT"
        if s is None or s["status"] != "OK":
            continue
        r["short_rounds"], r["short_seconds"] = s["rounds"], s["seconds"]
        new = acc01.shorten(starts[cid], s["path"], ball)
        final, work, ok = acc01.replay(starts[cid], new)
        if final != acc01.TARGET or not ok:
            r["short_status"] = "BAD_REPLAY"
            continue
        if len(new) < len(r["path"]):
            r.update({"path": new, "length": len(new), "work": work, "replay_ok": True})


def solve(items, args, ball):
    """acc02's passes A and B, then pass C on what they leave; rows in the order of items."""
    rows = acc02.solve_all(items, args, ball)
    left = [(cid, desc) for (cid, desc), r in zip(items, rows)
            if "path" not in r and r["status"] != "PARSE_ERROR"]
    if not left:
        return rows
    c_args = copy.copy(args)
    c_args.b_seconds, c_args.nodes = args.c_seconds, args.c_nodes
    saved = acc02.PASSES
    acc02.PASSES = (PASS_C,)
    try:
        crows = {r["challenge_id"]: r for r in acc02.solve_all(left, c_args, ball)}
    finally:
        acc02.PASSES = saved
    for r in rows:
        c = crows.get(r["challenge_id"])
        if c is None:
            continue
        r.update({k: v for k, v in c.items() if k.startswith("C_")})
        r["status"] = c["status"]
        if "path" in c:
            r.update({k: c[k] for k in ("path", "length", "work", "replay_ok", "pass")})
    return rows


def has_error(row):
    """A self-check failed: a search's replay (ERROR), the Python replay or finish, no output, or
    the shortener (ERROR, no output, or a shortened path that acc01's moves do not replay)."""
    return (row["status"] == "NO_OUTPUT"
            or any(row.get(f"{p}_status") == "ERROR" for p in PASS_NAMES)
            or any(row.get(f"{p}_finish") in ("BAD_REPLAY", "BAD_FINISH") for p in PASS_NAMES)
            or row.get("short_status") in ("ERROR", "NO_OUTPUT", "BAD_REPLAY"))


def length_stats(xs):
    xs = sorted(xs)
    if not xs:
        return {"n": 0}
    return {"n": len(xs), "median": xs[len(xs) // 2], "mean": round(sum(xs) / len(xs), 1),
            "max": xs[-1], "sum": sum(xs)}


def bucket(total):
    return "le20" if total <= 20 else "ge30" if total >= 30 else "21_29"


# ---------- the parts ----------

def run_control(args):
    g, info = {}, {}
    ok, tail = build()
    g["build_selftest"] = ok
    info["build_tail"] = tail
    train = acc01.read_jsonl(acc01.repo_path("competition", "examples", "ac.jsonl"))
    g["train_424"] = len(train) == 424
    if ok:
        rows = solve(train, args, acc01.BALL)
        shorten_rows(rows, starts_of(train, rows), args.workers, acc01.BALL)
        acc01.save(args.out_dir, "acc03_train_rows.json", rows)
        got, files = acc01.verify_lines(acc01.submission_lines(rows), acc01.TRAIN_MANIFEST,
                                        args.out_dir, "acc03_train")
        found = [r for r in rows if "path" in r]
        g["train_replay_ok"] = all(r["replay_ok"] for r in found)
        g["train_verified"] = all(got.get(r["challenge_id"], [False])[0] for r in found)
        g["train_lengths_agree"] = all(got.get(r["challenge_id"], [0, -1])[1] == r["length"]
                                       for r in found)
        g["train_no_error"] = not any(has_error(r) for r in rows)
        g["train_never_longer"] = all(r["length"] <= r["orig_length"] for r in found)
        info.update({"by_status": dict(collections.Counter(r["status"] for r in rows)),
                     "solved": len(found), "files": files,
                     "orig_lengths": length_stats([r["orig_length"] for r in found]),
                     "lengths": length_stats([r["length"] for r in found])})
    info["graded"] = g
    acc01.save(args.out_dir, "acc03_control.json", info)
    bad = sorted(k for k, v in g.items() if not v)
    print(f"SUMMARY control all_match {not bad} failed {bad} "
          f"{json.dumps({k: info.get(k) for k in ('by_status', 'orig_lengths', 'lengths')}, sort_keys=True)}",
          flush=True)


def run_search(args):
    ok, tail = build()
    if not ok:
        print(f"SUMMARY search build failed {tail}", flush=True)
        return
    items = acc02.shard_items(args.shard)
    t0 = time.time()
    rows = solve(items, args, acc01.BALL)
    t1 = time.time()
    shorten_rows(rows, starts_of(items, rows), args.workers, acc01.BALL)
    acc01.save(args.out_dir, f"acc03{args.shard}_rows.json", rows)
    by = collections.Counter(r["status"] for r in rows)
    print(f"SUMMARY search {args.shard} {len(rows)} {json.dumps(dict(by), sort_keys=True)} "
          f"search_seconds {round(t1 - t0)} shorten_seconds {round(time.time() - t1)}", flush=True)


def run_verify(args):
    rows = acc01.load(args.out_dir, f"acc03{args.shard}_rows.json") or []
    got, files = acc01.verify_lines(acc01.submission_lines(rows), acc01.OFFICIAL_MANIFEST,
                                    args.out_dir, f"acc03{args.shard}_sub")
    acc01.save(args.out_dir, f"acc03{args.shard}_verify.json", {"results": got, "files": files})
    ok = sum(v[0] for v in got.values())
    print(f"SUMMARY verify {args.shard} lines {sum(f['lines'] for f in files)} ok {ok} files "
          f"{len(files)} rcs {sorted(set(f['rc'] for f in files))}", flush=True)


def grade(args):
    g, out = {}, {}
    ctl = acc01.load(args.out_dir, "acc03_control.json")
    g["control_ran"] = ctl is not None
    if ctl:
        g.update({"control_" + k: v for k, v in ctl["graded"].items()})
        out["control_solved"] = ctl.get("solved")
        out["control_lengths"] = [ctl.get("orig_lengths"), ctl.get("lengths")]
    rows = acc01.load(args.out_dir, f"acc03{args.shard}_rows.json")
    ver = acc01.load(args.out_dir, f"acc03{args.shard}_verify.json")
    g["search_ran"] = rows is not None
    g["verify_ran"] = ver is not None
    rows, res = rows or [], (ver or {}).get("results", {})
    g["shard_size"] = len(rows) == len(acc02.shard_items(args.shard))
    g["no_parse_error"] = not any(r["status"] == "PARSE_ERROR" for r in rows)
    g["no_error"] = not any(has_error(r) for r in rows)
    found = [r for r in rows if "path" in r]
    g["replay_ok"] = all(r["replay_ok"] for r in found)
    g["ac_verified"] = all(res.get(r["challenge_id"], [False])[0] for r in found)
    g["sac_verified"] = all(res.get("s" + r["challenge_id"], [False])[0] for r in found)
    g["lengths_agree"] = all(res.get(r["challenge_id"], [0, -1])[1] == r["length"] for r in found)
    g["never_longer"] = all(r["length"] <= r["orig_length"] for r in found)
    buckets = {}
    for r in rows:
        if "start_total" in r:
            b = buckets.setdefault(bucket(r["start_total"]), [0, 0])
            b[0] += "path" in r
            b[1] += 1
    out.update({"by_status": dict(collections.Counter(r["status"] for r in rows)),
                "solved": len(found), "of": len(rows),
                "by_pass": dict(collections.Counter(r["pass"] for r in found)),
                "orig_lengths": length_stats([r["orig_length"] for r in found]),
                "lengths": length_stats([r["length"] for r in found]),
                "short_status": dict(collections.Counter(r.get("short_status") for r in found)),
                "shortened": sum(r["length"] < r["orig_length"] for r in found),
                "solved_by_bucket": buckets,
                "seconds": round(sum(r.get(f"{p}_seconds", 0) for r in rows for p in PASS_NAMES),
                                 1)})
    out["graded"] = g
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["build", "control", "search", "verify", "grade"],
                    default="build")
    ap.add_argument("--shard", choices=list(acc02.SHARDS), default="a")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--a-seconds", type=float, default=1.5)
    ap.add_argument("--b-seconds", type=float, default=4.0)
    ap.add_argument("--c-seconds", type=float, default=10.0)
    ap.add_argument("--nodes", type=int, default=1500000)
    ap.add_argument("--c-nodes", type=int, default=3000000)
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    if args.part == "build":
        ok, tail = build()
        print(tail, flush=True)
        print(f"SUMMARY build {ok}", flush=True)
        sys.exit(0 if ok else 1)
    if args.part in ("control", "search"):
        acc01.BALL.update(acc01.build_ball(5))
    if args.part == "control":
        run_control(args)
    elif args.part == "search":
        run_search(args)
    elif args.part == "verify":
        run_verify(args)
    else:
        out = grade(args)
        acc01.save(args.out_dir, f"acc03{args.shard}_grade.json", out)
        bad = sorted(k for k, v in out["graded"].items() if not v)
        extra = {k: v for k, v in out.items() if k != "graded"}
        print(f"SUMMARY grade {args.shard} all_match {not bad} graded {len(out['graded'])} "
              f"failed {bad} {json.dumps(extra, sort_keys=True)}", flush=True)


if __name__ == "__main__":
    main()
