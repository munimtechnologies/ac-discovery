# Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Job acc06 (pilot): does a beam search over the verifier's own moves find shorter Andrews-Curtis
paths than MV2's class search plus shortcuts? SAIR / Caltech Andrews-Curtis Conjecture Challenge,
Discovery Track (github.com/SAIRcompetition/Andrews-Curtis, Apache-2.0; deadline 2026-11-30).
Predictions in acc06-predictions.md, written before the job ran.

What came back on 2026-10-28: MV2's first 25 upload files (acc03's paths for all four shards and
acc04's shorter ones) were accepted, but the leaderboard then gave him 29 scoring challenges against
5,500 or more for the leading teams. Only the shortest verified path on a challenge scores, so his
paths (median 181 to 193 moves after acc05's radius-4 stages, graded in four of eight shards) are
longer than the leaders' on almost every challenge. acc02.c searches pairs of relators up to
rotation and pays for the rotations afterwards; acc03.c only cuts detours locally. acc06.c instead
keeps the --width shortest states at every level of the verifier's moves (see its header), so a
path found at level L has exactly L moves.

    beam     acc06.c at three widths (w1k, w8k, w64k) on the same presentations
    s33      acc03.c (r1 = r2 = 3) on every beam path, then acc01's cut at the target's ball; the
             shorter path is kept only if acc01's moves replay it to exactly (x, y)
    compare  the shortest path per presentation against acc05a0's final length (ref_acc05a0.json,
             lengths only, taken from acc05a0's rows; kept with the job and not published while
             the challenge runs)
    verify   every final path, as AC and as Stable AC, through the challenge's verifier and the
             official manifest; the paths strictly shorter than acc05a0's (or for presentations it
             did not solve) also go into their own files, for upload

The presentations are the first --n of acc05's shard a0 (acc02's shard a, every second one).
Paths stay private until the challenge closes; only counts are published.

Usage: python acc06.py --part pilot|grade [--n N] [--workers W] [--minutes M] [--out-dir D]
       (acc01.py to acc05.py, acc02.c and acc03.c of ac-discovery, and the challenge repository
       unpacked by acc01's fetch, in the working directory)
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
import acc04
import acc05

BEAM = os.path.abspath("acc06")
CONFIGS = (("w1k", ["--width", "1000", "--max-depth", "600", "--seconds", "15"]),
           ("w8k", ["--width", "8000", "--max-depth", "600", "--seconds", "30"]),
           ("w64k", ["--width", "64000", "--max-depth", "300", "--seconds", "45"]))
CONFIG_NAMES = tuple(c for c, _ in CONFIGS)
REF_FILE = "ref_acc05a0.json"
BEAM_SHARE = 0.75               # of --minutes for the beams; the rest for s33


def build():
    """acc03's build and self-tests (acc02.c, acc03.c), then gcc -O2 acc06.c and its self-test."""
    ok, tail = acc03.build()
    if not ok:
        return False, tail
    p = subprocess.run(["gcc", "-O2", "-o", BEAM, "acc06.c"], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    if p.returncode:
        return False, p.stdout[-2000:]
    p = subprocess.run([BEAM, "--selftest", "--width", "2000"], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True, timeout=1200)
    return p.returncode == 0 and "SELFTEST ok" in p.stdout, tail + p.stdout[-1000:]


def parse_beam(line):
    """{'id', 'status', 'length', 'levels', 'seconds', 'path'} from a line of acc06.c."""
    f = line.split()
    path = [] if f[5] == "-" else [int(m) for m in f[5].split(",")]
    return {"id": f[0], "status": f[1], "length": int(f[2]), "levels": int(f[3]),
            "seconds": float(f[4]), "path": path}


def run_beam(starts, ids, workers, opts, deadline):
    """{id: parsed line} from acc06.c on {id: (r0, r1)}, in the order of ids, split over `workers`
    processes; processes still running at the deadline are killed and only their complete lines
    are kept (acc06.c flushes after every line)."""
    parts = [ids[k::workers] for k in range(workers)]
    procs, outs, got = [], [], {}
    with tempfile.TemporaryDirectory() as d:
        for k, part in enumerate(parts):
            if not part:
                continue
            src = os.path.join(d, f"in{k}.txt")
            with open(src, "w") as f:
                for cid in part:
                    r0, r1 = starts[cid]
                    f.write(f"{cid} {acc02.to_str(r0)} {acc02.to_str(r1)}\n")
            out = open(os.path.join(d, f"out{k}.txt"), "w+")
            procs.append(subprocess.Popen([BEAM] + opts, stdin=open(src), stdout=out))
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
                    r = parse_beam(line)
                except (IndexError, ValueError):
                    continue
                got[r["id"]] = r
            out.close()
    return got


def load_ref():
    with open(REF_FILE) as f:
        return json.load(f)["lengths"]


def items_of(n):
    return acc05.items_of("a", 0)[:n]


def run_pilot(args):
    t0 = time.time()
    deadline = t0 + args.minutes * 60
    beam_deadline = t0 + args.minutes * 60 * BEAM_SHARE
    ok, tail = build()
    info = {"build_selftest": ok, "build_tail": tail, "seconds": {}}
    if not ok:
        acc01.save(args.out_dir, "acc06_pilot.json", info)
        print(f"SUMMARY pilot build failed {tail[-600:]}", flush=True)
        return
    items = items_of(args.n)
    ref = load_ref()
    starts, rows = {}, []
    for cid, desc in items:
        row = {"challenge_id": cid, "ref": ref.get(cid)}
        try:
            starts[cid] = acc01.parse(desc)
            row["start_total"] = acc01.total(starts[cid])
        except ValueError as e:
            row.update({"status": "PARSE_ERROR", "reason": str(e)})
        rows.append(row)
    ids = [r["challenge_id"] for r in rows if r["challenge_id"] in starts]
    byid = {r["challenge_id"]: r for r in rows}
    for k, (name, opts) in enumerate(CONFIGS):
        t1 = time.time()
        # each width gets an equal share of what is left of the beams' budget
        stop = t1 + (beam_deadline - t1) / (len(CONFIGS) - k)
        got = run_beam(starts, ids, args.workers, opts, stop)
        info["seconds"][name] = round(time.time() - t1)
        for cid in ids:
            r, b = byid[cid], got.get(cid)
            if b is None:
                r[name] = {"status": "NOT_REACHED"}
                continue
            c = {"status": b["status"], "levels": b["levels"], "seconds": b["seconds"]}
            if b["status"] == "SOLVED":
                final, work, okr = acc01.replay(starts[cid], b["path"])
                if final != acc01.TARGET or not okr or len(b["path"]) != b["length"]:
                    c["status"] = "BAD_REPLAY"
                else:
                    c.update({"length": b["length"], "path": b["path"]})
            r[name] = c
        print(f"beam {name}: {len(got)} of {len(ids)} reached, "
              f"{sum(byid[c][name]['status'] == 'SOLVED' for c in ids)} solved, "
              f"{info['seconds'][name]} s", flush=True)
    t1 = time.time()
    for name in CONFIG_NAMES:
        jobs = {cid: (starts[cid], byid[cid][name]["path"]) for cid in ids
                if "path" in byid[cid][name]}
        got = acc04.run_short_until(jobs, args.workers, acc03.SHORT_OPTS, deadline)
        for cid in jobs:
            c, s = byid[cid][name], got.get(cid)
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
        best = None
        for name in CONFIG_NAMES:
            c = r.get(name, {})
            if "path" in c and (best is None or len(c["path"]) < len(best[1])):
                best = (name, c["path"])
        for name in CONFIG_NAMES:
            r.get(name, {}).pop("path", None)
        if best is not None:
            final, work, okr = acc01.replay(starts[r["challenge_id"]], best[1])
            r.update({"best_config": best[0], "path": best[1], "length": len(best[1]),
                      "work": work, "replay_ok": final == acc01.TARGET and okr})
    acc01.save(args.out_dir, "acc06_rows.json", rows)
    got, files = acc01.verify_lines(acc01.submission_lines(rows), acc01.OFFICIAL_MANIFEST,
                                    args.out_dir, "acc06_all")
    better = [r for r in rows if "path" in r and (r["ref"] is None or r["length"] < r["ref"])]
    got_b, files_b = acc01.verify_lines(acc01.submission_lines(better), acc01.OFFICIAL_MANIFEST,
                                        args.out_dir, "acc06_better_sub")
    acc01.save(args.out_dir, "acc06_verify.json", {"results": got, "files": files,
                                                   "better_results": got_b, "better_files": files_b})
    info.update({"items": len(items), "files": [{k: f[k] for k in ("file", "lines", "rc")}
                                                for f in files + files_b]})
    acc01.save(args.out_dir, "acc06_pilot.json", info)
    print(f"SUMMARY pilot items {len(items)} solved {sum('path' in r for r in rows)} better "
          f"{len(better)} seconds {json.dumps(info['seconds'], sort_keys=True)}", flush=True)


# ---------- grading ----------

def config_stats(rows, name):
    """Counts and lengths for one width, raw and after s33, and against acc05a0 where both solved."""
    cs = [r.get(name, {}) for r in rows]
    solved = [(r, c) for r, c in zip(rows, cs) if c.get("status") == "SOLVED"]
    both = [(r, c) for r, c in solved if r["ref"] is not None]
    secs = sorted(c["seconds"] for c in cs if "seconds" in c)
    return {"status": dict(collections.Counter(c.get("status", "MISSING") for c in cs)),
            "solved": len(solved),
            "new_vs_ref": sum(r["ref"] is None for r, _ in solved),
            "lengths": acc03.length_stats([c["length"] for _, c in solved]),
            "s33_lengths": acc03.length_stats([c["s33_length"] for _, c in solved
                                               if "s33_length" in c]),
            "both_solved": len(both),
            "both_sum_s33": sum(c.get("s33_length", c["length"]) for _, c in both),
            "both_sum_ref": sum(r["ref"] for r, _ in both),
            "shorter_than_ref": sum(c.get("s33_length", c["length"]) < r["ref"] for r, c in both),
            "seconds_mean": round(sum(secs) / len(secs), 2) if secs else None,
            "seconds_max": secs[-1] if secs else None}


def grade(args):
    g, out = {}, {}
    info = acc01.load(args.out_dir, "acc06_pilot.json")
    rows = acc01.load(args.out_dir, "acc06_rows.json")
    ver = acc01.load(args.out_dir, "acc06_verify.json")
    g["pilot_ran"] = info is not None and rows is not None and ver is not None
    g["build_selftest"] = bool(info and info.get("build_selftest"))
    rows, ver = rows or [], ver or {}
    res, res_b = ver.get("results", {}), ver.get("better_results", {})
    g["items"] = len(rows) == args.n
    g["no_parse_error"] = not any(r.get("status") == "PARSE_ERROR" for r in rows)
    g["no_beam_error"] = not any(r.get(n, {}).get("status") in ("ERROR", "SKIP", "BAD_REPLAY")
                                 for r in rows for n in CONFIG_NAMES)
    g["no_s33_error"] = not any(r.get(n, {}).get("s33_status") in ("ERROR", "BAD_REPLAY")
                                for r in rows for n in CONFIG_NAMES)
    found = [r for r in rows if "path" in r]
    g["some_solved"] = bool(found)
    g["replay_ok"] = all(r["replay_ok"] for r in found)
    g["ac_verified"] = all(res.get(r["challenge_id"], [False])[0] for r in found)
    g["sac_verified"] = all(res.get("s" + r["challenge_id"], [False])[0] for r in found)
    g["lengths_agree"] = all(res.get(r["challenge_id"], [0, -1])[1] == r["length"] for r in found)
    better = [r for r in found if r["ref"] is None or r["length"] < r["ref"]]
    g["better_verified"] = all(res_b.get(r["challenge_id"], [False])[0]
                               and res_b.get("s" + r["challenge_id"], [False])[0] for r in better)
    g["s33_never_longer"] = all(r[n]["s33_length"] <= r[n]["length"] for r in rows
                                for n in CONFIG_NAMES if "s33_length" in r.get(n, {}))
    ref_solved = [r for r in rows if r["ref"] is not None]
    both = [r for r in ref_solved if "path" in r]
    combined = sum(min(r["length"], r["ref"]) if "path" in r else r["ref"] for r in ref_solved)
    out.update({
        "items": len(rows),
        "ref_solved": len(ref_solved),
        "ref_sum": sum(r["ref"] for r in ref_solved),
        "solved_any_width": len(found),
        "new_vs_ref": sum(r["ref"] is None for r in found),
        "both_solved": len(both),
        "both_sum_best": sum(r["length"] for r in both),
        "both_sum_ref": sum(r["ref"] for r in both),
        "better": len(better),
        "shorter_than_ref": sum(r["length"] < r["ref"] for r in both),
        "combined_sum": combined,
        "best_config": dict(collections.Counter(r["best_config"] for r in found)),
        "configs": {n: config_stats(rows, n) for n in CONFIG_NAMES},
        "seconds": (info or {}).get("seconds"),
        "files": (info or {}).get("files")})
    out["graded"] = g
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["pilot", "grade"], default="pilot")
    ap.add_argument("--n", type=int, default=240)
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
        acc01.save(args.out_dir, "acc06_grade.json", out)
        bad = sorted(k for k, v in out["graded"].items() if not v)
        extra = {k: v for k, v in out.items() if k != "graded"}
        print(f"SUMMARY grade all_match {not bad} graded {len(out['graded'])} failed {bad} "
              f"{json.dumps(extra, sort_keys=True)}", flush=True)


if __name__ == "__main__":
    main()
