# Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Job acc01: a first pass of MV2's searches over the 10,115 balanced two-generator presentations of
the SAIR / Caltech Andrews-Curtis Conjecture Challenge, Discovery Track (github.com/SAIRcompetition/
Andrews-Curtis, Apache-2.0; deadline 2026-11-30), with every path checked by the challenge's own
verifier (predictions in acc01-predictions.md, written before the job ran).

A state is a pair of freely reduced words (r0, r1) in x = 1, x^-1 = -1, y = 2, y^-1 = -2. The 14 AC
moves are the verifier's (competition/tools/verifier/README.md, move set ac-r2-v1):

    0  r0 -> r0^-1          1  r1 -> r1^-1
    2  r0 -> r0 r1          3  r0 -> r0 r1^-1        4  r1 -> r1 r0        5  r1 -> r1 r0^-1
    6  r0 -> x r0 x^-1      7  r0 -> x^-1 r0 x       8  r0 -> y r0 y^-1    9  r0 -> y^-1 r0 y
    10 r1 -> x r1 x^-1      11 r1 -> x^-1 r1 x       12 r1 -> y r1 y^-1    13 r1 -> y^-1 r1 y

and the target is exactly (x, y). Each move is undone by INV[move], so the states within distance R
of the target are the states the target reaches in R moves.

Two searches per presentation:

    bfs   exact: every state within R moves of the target (built once), and breadth-first layers
          from the presentation up to depth F (or a node cap). If layer j0 is the first that meets
          the target's ball, the shortest path has length min over that layer of j0 + dist(s): a
          shortest path of length L > R passes, after L - R moves, a state at distance L - R from
          the start and R from the target, so j0 <= L - R and the minimum (at most j0 + R) is L.
          Proven shortest only if every layer up to j0 was complete.
    gs    greedy best-first search (priority: total relator length, then moves so far), as the
          baseline of Shehper et al., arXiv:2408.15332, with a node and time cap; the path found is
          cut at its first state inside the target's ball and finished by the ball's shortest path.

Parts:

    fetch     the challenge repository at the head of main (commit recorded), unpacked under acc_repo/
    control   the sample paths of examples/sample_submission.txt replayed by acc01's moves; the
              searches on the 424 training presentations; the verifier on its own sample and on
              every training path found (training manifest), and its hash check of both manifests
    search    the 10,115 AC presentations, two processes, with the same caps
    verify    every path found, as submission files of at most 500 lines (AC, and Stable AC = the
              AC path then moves 16, 15, as the sample does), through the verifier and the official
              manifest
    grade     the graded checks of acc01-predictions.md

Usage: python acc01.py --part fetch|control|search|verify|grade [--radius R] [--depth F]
       [--gs-nodes N] [--gs-seconds S] [--workers W] [--out-dir D]
"""
import argparse
import collections
import heapq
import io
import json
import multiprocessing as mp
import os
import re
import subprocess
import sys
import tarfile
import time
import urllib.request

REPO = "SAIRcompetition/Andrews-Curtis"
ROOT = "acc_repo"
TARGET = ((1,), (2,))
INV = (0, 1, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12)
MAX_TOTAL = 10000              # the verifier's limits (rules/discovery.md)
MAX_WORK = 5000000
MAX_MOVES = 100000
LINES_PER_FILE = 500
SAC_TAIL = [16, 15]            # destabilize relator 1 (y), then relator 0 (x): sample_submission.txt
TOKENS = {"x": 1, "x^-1": -1, "y": 2, "y^-1": -2}


def save(out_dir, name, obj):
    with open(os.path.join(out_dir, name), "w") as f:
        json.dump(obj, f, indent=1)


def load(out_dir, name):
    path = os.path.join(out_dir, name)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


# ---------- words and moves ----------

def join(a, b):
    """The free reduction of a b for reduced words a, b (cancellation only at the junction)."""
    i, n = 0, min(len(a), len(b))
    while i < n and a[-1 - i] == -b[i]:
        i += 1
    return a[:len(a) - i] + b[i:]


def reduce_word(w):
    out = []
    for a in w:
        if out and out[-1] == -a:
            out.pop()
        else:
            out.append(a)
    return tuple(out)


def inv(w):
    return tuple(-a for a in reversed(w))


def conj(g, w):
    """g w g^-1, reduced."""
    return join(join((g,), w), (-g,))


def apply(state, m):
    r0, r1 = state
    if m == 0:
        return inv(r0), r1
    if m == 1:
        return r0, inv(r1)
    if m == 2:
        return join(r0, r1), r1
    if m == 3:
        return join(r0, inv(r1)), r1
    if m == 4:
        return r0, join(r1, r0)
    if m == 5:
        return r0, join(r1, inv(r0))
    g = (1, -1, 2, -2)[(m - 6) % 4]
    if m < 10:
        return conj(g, r0), r1
    return r0, conj(g, r1)


def total(state):
    return len(state[0]) + len(state[1])


def parse(description):
    """(r0, r1) from 'Presentation: <x, y | w0 = 1; w1 = 1>' (tokens x, y, x^-1, y^-1, 1)."""
    m = re.search(r"<\s*x\s*,\s*y\s*\|(.*)>", description)
    if not m:
        raise ValueError(f"not a two-generator presentation: {description!r}")
    rels = [r.strip() for r in m.group(1).split(";")]
    if len(rels) != 2:
        raise ValueError(f"not two relators: {description!r}")
    out = []
    for r in rels:
        if not r.endswith("= 1"):
            raise ValueError(f"relator not written as w = 1: {r!r}")
        word = []
        for tok in r[:-3].split():
            if tok == "1":
                continue
            if tok not in TOKENS:
                raise ValueError(f"unknown token {tok!r}")
            word.append(TOKENS[tok])
        out.append(reduce_word(word))
    return tuple(out)


def replay(state, path):
    """(final state, work, ok within the limits): the verifier's rules, as acc01 reads them."""
    work, ok = total(state), len(path) <= MAX_MOVES
    for m in path:
        state = apply(state, m)
        work += total(state)
        ok = ok and total(state) <= MAX_TOTAL
    return state, work, ok and work <= MAX_WORK


# ---------- the target's ball ----------

def build_ball(radius):
    """{state: (distance to the target, move that takes it one step closer, or None)}."""
    ball = {TARGET: (0, None)}
    layer = [TARGET]
    for d in range(1, radius + 1):
        nxt = []
        for s in layer:
            for m in range(14):
                t = apply(s, m)
                if t not in ball:
                    ball[t] = (d, INV[m])
                    nxt.append(t)
        layer = nxt
    return ball


def ball_path(ball, state):
    path = []
    while state != TARGET:
        m = ball[state][1]
        path.append(m)
        state = apply(state, m)
    return path


def back_path(parent, state):
    path = []
    while parent[state] is not None:
        prev, m = parent[state]
        path.append(m)
        state = prev
    return path[::-1]


# ---------- the two searches ----------

def bfs(start, ball, depth, cap):
    """(path or None, proven shortest, states seen)."""
    parent = {start: None}
    layer, complete = [start], True
    for j in range(depth + 1):
        hits = [s for s in layer if s in ball]
        if hits:
            best = min(hits, key=lambda s: (ball[s][0], s))
            return back_path(parent, best) + ball_path(ball, best), complete, len(parent)
        if j == depth:
            break
        nxt = []
        for s in layer:
            for m in range(14):
                t = apply(s, m)
                if t not in parent:
                    if len(parent) >= cap:
                        complete = False
                        break
                    parent[t] = (s, m)
                    nxt.append(t)
            if not complete:
                break
        layer = nxt
        if not complete:
            # the partial layer is still searched once for a meeting, but proves nothing
            hits = [s for s in layer if s in ball]
            if hits:
                best = min(hits, key=lambda s: (ball[s][0], s))
                return back_path(parent, best) + ball_path(ball, best), False, len(parent)
            break
    return None, False, len(parent)


def gs(start, ball, nodes, seconds, max_total):
    """(path or None, nodes popped): greedy best-first by total length, stopped at the ball."""
    t0 = time.time()
    parent = {start: None}
    heap = [(total(start), 0, 0, start)]
    count = popped = 0
    while heap and popped < nodes and time.time() - t0 < seconds:
        _, g, _, s = heapq.heappop(heap)
        popped += 1
        if s in ball:
            return back_path(parent, s) + ball_path(ball, s), popped
        for m in range(14):
            t = apply(s, m)
            if t in parent or total(t) > max_total:
                continue
            parent[t] = (s, m)
            count += 1
            heapq.heappush(heap, (total(t), g + 1, count, t))
    return None, popped


def shorten(start, path, ball):
    """Cut a path at its first state inside the ball and finish with the ball's shortest path."""
    s = start
    for i in range(len(path) + 1):
        if s in ball:
            return path[:i] + ball_path(ball, s)
        if i < len(path):
            s = apply(s, path[i])
    return path


BALL = {}


def solve(item, depth, cap, gs_nodes, gs_seconds):
    cid, desc = item
    t0 = time.time()
    row = {"challenge_id": cid}
    try:
        start = parse(desc)
    except ValueError as e:
        row.update({"status": "PARSE_ERROR", "reason": str(e)})
        return row
    row["start_total"] = total(start)
    path, proven, seen = bfs(start, BALL, depth, cap)
    row["bfs_states"] = seen
    if path is not None:
        row.update({"status": "OPTIMAL" if proven else "BFS", "path": path})
    else:
        max_total = max(4 * total(start), total(start) + 40)
        path, popped = gs(start, BALL, gs_nodes, gs_seconds, max_total)
        row["gs_nodes"] = popped
        if path is not None:
            row.update({"status": "GS", "path": shorten(start, path, BALL)})
        else:
            row["status"] = "NONE"
    if "path" in row:
        final, work, ok = replay(start, row["path"])
        row.update({"length": len(row["path"]), "work": work,
                    "replay_ok": final == TARGET and ok})
    row["seconds"] = round(time.time() - t0, 3)
    return row


def _solve_star(args):
    return solve(*args)


def run_all(items, args):
    jobs = [(it, args.depth, args.bfs_cap, args.gs_nodes, args.gs_seconds) for it in items]
    if args.workers <= 1:
        return [_solve_star(j) for j in jobs]
    # fork: the workers share the ball built in the parent
    with mp.get_context("fork").Pool(args.workers) as pool:
        return list(pool.imap(_solve_star, jobs, chunksize=8))


# ---------- the challenge's files and verifier ----------

def repo_path(*parts):
    return os.path.join(ROOT, *parts)


def read_jsonl(path):
    with open(path) as f:
        return [(o["challenge_id"], o["description"]) for o in map(json.loads, filter(str.strip, f))]


def submission_lines(rows, stable=True):
    out = []
    for r in rows:
        if r.get("replay_ok"):
            out.append(f"{r['challenge_id']}: [{', '.join(map(str, r['path']))}]")
            if stable:
                sid = "s" + r["challenge_id"] if r["challenge_id"].startswith("ac-") else (
                    r["challenge_id"].replace("ms-train", "sac-train"))
                out.append(f"{sid}: [{', '.join(map(str, r['path'] + SAC_TAIL))}]")
    return out


def chunks(lines, n=LINES_PER_FILE):
    return [lines[i:i + n] for i in range(0, len(lines), n)]


def run_verifier(manifest, submission):
    """(exit code, parsed JSON or None, tail of output) from the challenge's own verifier."""
    env = dict(os.environ, PYTHONPATH=os.path.abspath(repo_path("competition", "tools")))
    cmd = [sys.executable, "-m", "verifier", "--manifest", manifest, "--submission",
           os.path.abspath(submission), "--pretty"]
    p = subprocess.run(cmd, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, timeout=3600)
    try:
        return p.returncode, json.loads(p.stdout), None
    except ValueError:
        return p.returncode, None, p.stdout[-2000:]


def verify_lines(lines, manifest, out_dir, tag):
    """{challenge_id: [ok, length]} and per-file exit codes for the lines, 500 per file."""
    got, files = {}, []
    for k, part in enumerate(chunks(lines)):
        path = os.path.join(out_dir, f"{tag}_{k + 1:03d}.txt")
        with open(path, "w") as f:
            f.write("# MV2 of Munim, Inc. (mv2@munimtech.com); paths found by AI agents working "
                    "in MV2's name\n" + "\n".join(part) + "\n")
        rc, res, tail = run_verifier(manifest, path)
        files.append({"file": os.path.basename(path), "lines": len(part), "rc": rc,
                      "accepted": (res or {}).get("accepted"), "tail": tail})
        for r in (res or {}).get("results", []):
            got[r["challenge_id"]] = [bool(r.get("ok")), r.get("length"), r.get("code")]
    return got, files


def check_hashes(manifest):
    env = dict(os.environ, PYTHONPATH=os.path.abspath(repo_path("competition", "tools")))
    p = subprocess.run([sys.executable, "-m", "verifier", "--manifest", manifest, "--check-hashes"],
                       cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, timeout=1800)
    return p.returncode, p.stdout[-600:]


TRAIN_MANIFEST = "competition/examples/training_manifest.json"
OFFICIAL_MANIFEST = "competition/tools/verifier/data/manifest.json"


# ---------- the parts ----------

def run_fetch(out_dir):
    with urllib.request.urlopen(f"https://api.github.com/repos/{REPO}/commits/main") as r:
        sha = json.load(r)["sha"]
    url = f"https://codeload.github.com/{REPO}/tar.gz/{sha}"
    with urllib.request.urlopen(url) as r:
        data = r.read()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        tops = {n.split("/")[0] for n in tf.getnames()}
        top = next(t for t in sorted(tops) if t.startswith("Andrews-Curtis"))
        tf.extractall("acc_tmp", filter="data")
    os.rename(os.path.join("acc_tmp", top), ROOT)
    n = {k: len(read_jsonl(repo_path("competition", *p))) for k, p in
         (("ac", ("problems", "ac.jsonl")), ("stable_ac", ("problems", "stable_ac.jsonl")),
          ("train", ("examples", "ac.jsonl")))}
    save(out_dir, "acc01_fetch.json", {"commit": sha, "bytes": len(data), "counts": n})
    print(f"SUMMARY fetch commit {sha} {json.dumps(n, sort_keys=True)}", flush=True)


def sample_paths():
    out = {}
    with open(repo_path("competition", "examples", "sample_submission.txt")) as f:
        for line in f:
            line = line.split("#")[0].strip()
            if line:
                cid, moves = line.split(":", 1)
                out[cid.strip()] = json.loads(moves)
    return out


def run_control(args):
    g, info = {}, {}
    train = read_jsonl(repo_path("competition", "examples", "ac.jsonl"))
    starts = {cid: parse(d) for cid, d in train}
    g["train_424"] = len(train) == 424
    replays = {}
    for cid, path in sample_paths().items():
        if cid in starts:
            final, _, ok = replay(starts[cid], path)
            replays[cid] = final == TARGET and ok
    g["sample_replays"] = bool(replays) and all(replays.values())
    rc, res, _ = run_verifier(TRAIN_MANIFEST, repo_path("competition", "examples",
                                                         "sample_submission.txt"))
    g["verifier_sample_ok"] = rc == 0 and bool(res) and all(r.get("ok") for r in res["results"])
    for name, man in (("train", TRAIN_MANIFEST), ("official", OFFICIAL_MANIFEST)):
        rc, tail = check_hashes(man)
        g[f"hashes_{name}"] = rc == 0
        info[f"hashes_{name}_tail"] = tail
    rows = run_all(train, args)
    save(args.out_dir, "acc01_train_rows.json", rows)
    got, files = verify_lines(submission_lines(rows), TRAIN_MANIFEST, args.out_dir, "acc01_train")
    found = [r for r in rows if "path" in r]
    g["train_replay_ok"] = all(r["replay_ok"] for r in found)
    g["train_verified"] = all(got.get(r["challenge_id"], [False])[0] for r in found)
    g["train_lengths_agree"] = all(got.get(r["challenge_id"], [0, -1])[1] == r["length"]
                                   for r in found)
    by = collections.Counter(r["status"] for r in rows)
    info.update({"by_status": dict(by), "files": files, "replays": replays, "graded": g})
    save(args.out_dir, "acc01_control.json", info)
    bad = sorted(k for k, v in g.items() if not v)
    print(f"SUMMARY control all_match {not bad} failed {bad} {json.dumps(dict(by), sort_keys=True)}",
          flush=True)


def run_search(args):
    items = read_jsonl(repo_path("competition", "problems", "ac.jsonl"))
    t0 = time.time()
    rows = run_all(items, args)
    save(args.out_dir, "acc01_rows.json", rows)
    by = collections.Counter(r["status"] for r in rows)
    print(f"SUMMARY search {len(rows)} {json.dumps(dict(by), sort_keys=True)} seconds "
          f"{round(time.time() - t0)}", flush=True)


def run_verify(out_dir):
    rows = load(out_dir, "acc01_rows.json") or []
    got, files = verify_lines(submission_lines(rows), OFFICIAL_MANIFEST, out_dir, "acc01_sub")
    save(out_dir, "acc01_verify.json", {"results": got, "files": files})
    ok = sum(v[0] for v in got.values())
    print(f"SUMMARY verify lines {sum(f['lines'] for f in files)} ok {ok} files {len(files)} "
          f"rcs {sorted(set(f['rc'] for f in files))}", flush=True)


def grade(out_dir):
    g, out = {}, {}
    ctl = load(out_dir, "acc01_control.json")
    g["control_ran"] = ctl is not None
    if ctl:
        g.update({"control_" + k: v for k, v in ctl["graded"].items()})
    rows = load(out_dir, "acc01_rows.json")
    ver = load(out_dir, "acc01_verify.json")
    g["search_ran"] = rows is not None
    g["verify_ran"] = ver is not None
    rows, res = rows or [], (ver or {}).get("results", {})
    g["all_10115"] = len(rows) == 10115
    g["no_parse_error"] = not any(r["status"] == "PARSE_ERROR" for r in rows)
    found = [r for r in rows if "path" in r]
    g["replay_ok"] = all(r["replay_ok"] for r in found)
    g["ac_verified"] = all(res.get(r["challenge_id"], [False])[0] for r in found)
    g["sac_verified"] = all(res.get("s" + r["challenge_id"], [False])[0] for r in found)
    g["lengths_agree"] = all(res.get(r["challenge_id"], [0, -1])[1] == r["length"] for r in found)
    by = collections.Counter(r["status"] for r in rows)
    lengths = collections.Counter(r["length"] for r in found if r["status"] == "OPTIMAL")
    gs_len = sorted(r["length"] for r in found if r["status"] == "GS")
    out.update({"by_status": dict(by), "solved": len(found),
                "optimal_lengths": dict(sorted(lengths.items())),
                "gs_lengths": {"n": len(gs_len), "median": gs_len[len(gs_len) // 2] if gs_len
                               else None, "max": gs_len[-1] if gs_len else None},
                "seconds": round(sum(r.get("seconds", 0) for r in rows), 1)})
    out["graded"] = g
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["fetch", "control", "search", "verify", "grade"],
                    default="control")
    ap.add_argument("--radius", type=int, default=5)
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--bfs-cap", type=int, default=20000)
    ap.add_argument("--gs-nodes", type=int, default=100000)
    ap.add_argument("--gs-seconds", type=float, default=1.0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    if args.part == "fetch":
        run_fetch(args.out_dir)
        return
    if args.part in ("control", "search"):
        t0 = time.time()
        BALL.update(build_ball(args.radius))
        print(f"ball radius {args.radius}: {len(BALL)} states, {round(time.time() - t0, 1)} s",
              flush=True)
    if args.part == "control":
        run_control(args)
    elif args.part == "search":
        run_search(args)
    elif args.part == "verify":
        run_verify(args.out_dir)
    else:
        out = grade(args.out_dir)
        save(args.out_dir, "acc01_grade.json", out)
        bad = sorted(k for k, v in out["graded"].items() if not v)
        extra = {k: v for k, v in out.items() if k != "graded"}
        print(f"SUMMARY grade all_match {not bad} graded {len(out['graded'])} failed {bad} "
              f"{json.dumps(extra, sort_keys=True)}", flush=True)


if __name__ == "__main__":
    main()
