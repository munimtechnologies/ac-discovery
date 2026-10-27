# Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Job acc02: MV2's second pass at the 10,115 presentations of the SAIR / Caltech Andrews-Curtis
Conjecture Challenge, Discovery Track (github.com/SAIRcompetition/Andrews-Curtis, Apache-2.0;
deadline 2026-11-30), with acc02.c's search on relators taken up to cyclic permutation and inversion
(predictions in acc02-predictions.md, written before the job ran).

acc01 (same repository) found paths for 418 of the 424 training presentations but only 180 of the
10,115 scored ones: its greedy search over the 14 explicit moves spent its nodes on conjugates of
the same state. acc02.c searches classes of states instead (see its header) and prints explicit
paths. This driver runs it in two passes per presentation:

    pass A    --grow 2 --slack 12   (a step may add at most 2 letters; at most 12 over the start)
    pass B    --grow 8 --slack 24   (only on what pass A left), with a longer time cap

and then, for every path found: replays it with acc01's moves (it must end at two single
letters), finishes it to exactly (x, y) with acc01's ball of radius 5 (or a breadth-first search of
depth 3 into the ball), cuts every loop (a state visited twice), cuts it at its first state
inside the ball and finishes with the ball's shortest path, and replays it again. Every path is
then checked by the challenge's verifier, as AC and as Stable AC (acc01.submission_lines).

Parts:

    build     gcc -O2 acc02.c; acc02 --selftest
    control   the 424 training presentations (both passes), every path through the verifier with
              the training manifest
    search    this shard's share of the 10,115 (index mod 4), both passes, two processes
    verify    every path found, through the verifier and the official manifest
    grade     the graded checks of acc02-predictions.md

Usage: python acc02.py --part build|control|search|verify|grade [--shard a..d] [--workers W]
       [--a-seconds S] [--b-seconds S] [--nodes N] [--out-dir D]
       (acc01.py and the challenge repository, unpacked by acc01's fetch, in the working directory)
"""
import argparse
import collections
import json
import os
import subprocess
import sys
import tempfile
import time

import acc01

SHARDS = "abcd"
LETTER = {1: "x", -1: "X", 2: "y", -2: "Y"}
BINARY = os.path.abspath("acc02")
PASSES = (("A", ["--grow", "2", "--slack", "12"]), ("B", ["--grow", "8", "--slack", "24"]))


def to_str(w):
    return "".join(LETTER[a] for a in w) or "-"


def parse_line(line):
    """{'id', 'status', 'pops', 'stored', 'moves', 'seconds', 'path'} from a line of acc02.c."""
    f = line.split()
    path = [] if f[6] == "-" else [int(m) for m in f[6].split(",")]
    return {"id": f[0], "status": f[1], "pops": int(f[2]), "stored": int(f[3]),
            "moves": int(f[4]), "seconds": float(f[5]), "path": path}


def build():
    p = subprocess.run(["gcc", "-O2", "-o", BINARY, "acc02.c"], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    if p.returncode:
        return False, p.stdout[-2000:]
    p = subprocess.run([BINARY, "--selftest", "--nodes", "200000"], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True, timeout=600)
    return p.returncode == 0 and "SELFTEST ok" in p.stdout, p.stdout[-2000:]


def run_c(starts, opts, workers, nodes):
    """{id: parsed line} from acc02.c on {id: (r0, r1)}, split over `workers` processes."""
    ids = sorted(starts)
    parts = [ids[k::workers] for k in range(workers)]
    procs, outs = [], []
    with tempfile.TemporaryDirectory() as d:
        for k, part in enumerate(parts):
            if not part:
                continue
            src = os.path.join(d, f"in{k}.txt")
            with open(src, "w") as f:
                for cid in part:
                    r0, r1 = starts[cid]
                    f.write(f"{cid} {to_str(r0)} {to_str(r1)}\n")
            out = open(os.path.join(d, f"out{k}.txt"), "w+")
            procs.append(subprocess.Popen([BINARY, "--nodes", str(nodes)] + opts,
                                          stdin=open(src), stdout=out))
            outs.append(out)
        for p in procs:
            p.wait()
        got = {}
        for out in outs:
            out.seek(0)
            for line in out:
                if line.strip():
                    r = parse_line(line)
                    got[r["id"]] = r
            out.close()
    return got


def cut_loops(start, path):
    """The path with every loop removed: from each state, jump to its last visit."""
    states = [start]
    for m in path:
        states.append(acc01.apply(states[-1], m))
    last = {s: k for k, s in enumerate(states)}
    out, k = [], 0
    while k < len(path):
        j = last[states[k]]
        if j > k:
            k = j
            continue
        out.append(path[k])
        k += 1
    return out


def finish(start, path, ball):
    """(full path to (x, y), status) for a path of acc02.c that ends at two single letters."""
    end, _, ok = acc01.replay(start, path)
    if not ok or len(end[0]) != 1 or len(end[1]) != 1:
        return None, "BAD_REPLAY"
    if end in ball:
        tail = acc01.ball_path(ball, end)
    else:
        tail, _, _ = acc01.bfs(end, ball, 3, 20000)
        if tail is None:
            return None, "UNFINISHED"
    full = acc01.shorten(start, cut_loops(start, path + tail), ball)
    final, _, ok = acc01.replay(start, full)
    if final != acc01.TARGET or not ok:
        return None, "BAD_FINISH"
    return full, "OK"


def solve_all(items, args, ball):
    """Rows for [(challenge_id, description)]: pass A, then pass B on what A left."""
    rows, starts = {}, {}
    for cid, desc in items:
        try:
            starts[cid] = acc01.parse(desc)
            rows[cid] = {"challenge_id": cid, "start_total": acc01.total(starts[cid])}
        except ValueError as e:
            rows[cid] = {"challenge_id": cid, "status": "PARSE_ERROR", "reason": str(e)}
    todo = dict(starts)
    for name, opts in PASSES:
        secs = args.a_seconds if name == "A" else args.b_seconds
        t0 = time.time()
        got = run_c(todo, opts + ["--seconds", str(secs)], args.workers, args.nodes)
        print(f"pass {name}: {len(todo)} presentations, {round(time.time() - t0)} s", flush=True)
        for cid in list(todo):
            r = got.get(cid)
            row = rows[cid]
            if r is None:
                row.update({"status": "NO_OUTPUT"})
                continue
            row[f"{name}_status"], row[f"{name}_pops"] = r["status"], r["pops"]
            row[f"{name}_seconds"] = r["seconds"]
            row["status"] = r["status"]
            if r["status"] != "SOLVED":
                continue
            full, how = finish(starts[cid], r["path"], ball)
            row.update({f"{name}_c_moves": r["moves"], f"{name}_finish": how})
            if full is None:
                row["status"] = how
                continue
            row["pass"] = name
            final, work, ok = acc01.replay(starts[cid], full)
            row.update({"path": full, "length": len(full), "work": work,
                        "replay_ok": final == acc01.TARGET and ok})
            del todo[cid]
    return [rows[cid] for cid, _ in items]


def has_error(row):
    """A self-check failed: acc02.c's replay (ERROR), the Python replay or finish, or no output."""
    return (row["status"] == "NO_OUTPUT"
            or any(row.get(f"{p}_status") == "ERROR" for p, _ in PASSES)
            or any(row.get(f"{p}_finish") in ("BAD_REPLAY", "BAD_FINISH") for p, _ in PASSES))


# ---------- the parts ----------

def run_control(args):
    g, info = {}, {}
    ok, tail = build()
    g["build_selftest"] = ok
    info["build_tail"] = tail
    train = acc01.read_jsonl(acc01.repo_path("competition", "examples", "ac.jsonl"))
    g["train_424"] = len(train) == 424
    if ok:
        rows = solve_all(train, args, acc01.BALL)
        acc01.save(args.out_dir, "acc02_train_rows.json", rows)
        got, files = acc01.verify_lines(acc01.submission_lines(rows), acc01.TRAIN_MANIFEST,
                                        args.out_dir, "acc02_train")
        found = [r for r in rows if "path" in r]
        g["train_replay_ok"] = all(r["replay_ok"] for r in found)
        g["train_verified"] = all(got.get(r["challenge_id"], [False])[0] for r in found)
        g["train_lengths_agree"] = all(got.get(r["challenge_id"], [0, -1])[1] == r["length"]
                                       for r in found)
        g["train_no_error"] = not any(has_error(r) for r in rows)
        info.update({"by_status": dict(collections.Counter(r["status"] for r in rows)),
                     "solved": len(found), "files": files})
    info["graded"] = g
    acc01.save(args.out_dir, "acc02_control.json", info)
    bad = sorted(k for k, v in g.items() if not v)
    print(f"SUMMARY control all_match {not bad} failed {bad} "
          f"{json.dumps(info.get('by_status'), sort_keys=True)}", flush=True)


def shard_items(shard):
    items = acc01.read_jsonl(acc01.repo_path("competition", "problems", "ac.jsonl"))
    k = SHARDS.index(shard)
    return [it for i, it in enumerate(items) if i % len(SHARDS) == k]


def run_search(args):
    ok, tail = build()
    if not ok:
        print(f"SUMMARY search build failed {tail}", flush=True)
        return
    items = shard_items(args.shard)
    t0 = time.time()
    rows = solve_all(items, args, acc01.BALL)
    acc01.save(args.out_dir, f"acc02{args.shard}_rows.json", rows)
    by = collections.Counter(r["status"] for r in rows)
    print(f"SUMMARY search {args.shard} {len(rows)} {json.dumps(dict(by), sort_keys=True)} "
          f"seconds {round(time.time() - t0)}", flush=True)


def run_verify(args):
    rows = acc01.load(args.out_dir, f"acc02{args.shard}_rows.json") or []
    got, files = acc01.verify_lines(acc01.submission_lines(rows), acc01.OFFICIAL_MANIFEST,
                                    args.out_dir, f"acc02{args.shard}_sub")
    acc01.save(args.out_dir, f"acc02{args.shard}_verify.json", {"results": got, "files": files})
    ok = sum(v[0] for v in got.values())
    print(f"SUMMARY verify {args.shard} lines {sum(f['lines'] for f in files)} ok {ok} files "
          f"{len(files)} rcs {sorted(set(f['rc'] for f in files))}", flush=True)


def grade(args):
    g, out = {}, {}
    ctl = acc01.load(args.out_dir, "acc02_control.json")
    g["control_ran"] = ctl is not None
    if ctl:
        g.update({"control_" + k: v for k, v in ctl["graded"].items()})
        out["control_solved"] = ctl.get("solved")
    rows = acc01.load(args.out_dir, f"acc02{args.shard}_rows.json")
    ver = acc01.load(args.out_dir, f"acc02{args.shard}_verify.json")
    g["search_ran"] = rows is not None
    g["verify_ran"] = ver is not None
    rows, res = rows or [], (ver or {}).get("results", {})
    g["shard_size"] = len(rows) == len(shard_items(args.shard))
    g["no_parse_error"] = not any(r["status"] == "PARSE_ERROR" for r in rows)
    g["no_error"] = not any(has_error(r) for r in rows)
    found = [r for r in rows if "path" in r]
    g["replay_ok"] = all(r["replay_ok"] for r in found)
    g["ac_verified"] = all(res.get(r["challenge_id"], [False])[0] for r in found)
    g["sac_verified"] = all(res.get("s" + r["challenge_id"], [False])[0] for r in found)
    g["lengths_agree"] = all(res.get(r["challenge_id"], [0, -1])[1] == r["length"] for r in found)
    lengths = sorted(r["length"] for r in found)
    out.update({"by_status": dict(collections.Counter(r["status"] for r in rows)),
                "solved": len(found), "of": len(rows),
                "by_pass": dict(collections.Counter(r["pass"] for r in found)),
                "lengths": {"n": len(lengths),
                            "median": lengths[len(lengths) // 2] if lengths else None,
                            "max": lengths[-1] if lengths else None},
                "solved_by_start_total": dict(sorted(collections.Counter(
                    r["start_total"] for r in found).items())),
                "seconds": round(sum(r.get("A_seconds", 0) + r.get("B_seconds", 0)
                                     for r in rows), 1)})
    out["graded"] = g
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["build", "control", "search", "verify", "grade"],
                    default="build")
    ap.add_argument("--shard", choices=list(SHARDS), default="a")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--a-seconds", type=float, default=1.5)
    ap.add_argument("--b-seconds", type=float, default=4.0)
    ap.add_argument("--nodes", type=int, default=1500000)
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
        acc01.save(args.out_dir, f"acc02{args.shard}_grade.json", out)
        bad = sorted(k for k, v in out["graded"].items() if not v)
        extra = {k: v for k, v in out.items() if k != "graded"}
        print(f"SUMMARY grade {args.shard} all_match {not bad} graded {len(out['graded'])} "
              f"failed {bad} {json.dumps(extra, sort_keys=True)}", flush=True)


if __name__ == "__main__":
    main()
