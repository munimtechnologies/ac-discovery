# Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Unit tests for acc01.py (job acc01, acc01-predictions.md). The moves are checked on words worked
out by hand from the verifier's move table, the searches on presentations built from the target by
known moves, and (once the fetch step has unpacked the challenge repository) the sample paths of
examples/sample_submission.txt replayed on the training presentations."""
import os
import unittest

import acc01 as a

X, XI, Y, YI = 1, -1, 2, -2


class TestWords(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(a.parse("Presentation: <x, y | x y = 1; y = 1>"), ((X, Y), (Y,)))
        self.assertEqual(a.parse("Presentation: <x, y | y^-1 x^-1 y x = 1; x x^-1 y = 1>"),
                         ((YI, XI, Y, X), (Y,)))
        with self.assertRaises(ValueError):
            a.parse("Presentation: <x, y | x^2 = 1; y = 1>")
        with self.assertRaises(ValueError):
            a.parse("Presentation: <x, y | x = y; y = 1>")

    def test_reduce_and_join(self):
        self.assertEqual(a.reduce_word((X, Y, YI, XI, Y)), (Y,))
        self.assertEqual(a.join((X, Y), (YI, XI, Y)), (Y,))
        self.assertEqual(a.join((X,), (X,)), (X, X))
        self.assertEqual(a.inv((X, Y, Y)), (YI, YI, XI))

    def test_moves_by_hand(self):
        s = ((X, Y), (Y, Y))
        want = {0: ((YI, XI), (Y, Y)), 1: ((X, Y), (YI, YI)),
                2: ((X, Y, Y, Y), (Y, Y)), 3: ((X, YI), (Y, Y)),
                4: ((X, Y), (Y, Y, X, Y)), 5: ((X, Y), (Y, XI)),
                6: ((X, X, Y, XI), (Y, Y)), 7: ((Y, X), (Y, Y)),
                8: ((Y, X), (Y, Y)), 9: ((YI, X, Y, Y), (Y, Y)),
                10: ((X, Y), (X, Y, Y, XI)), 11: ((X, Y), (XI, Y, Y, X)),
                12: ((X, Y), (Y, Y)), 13: ((X, Y), (Y, Y))}
        # 5: y y (x y)^-1 = y y y^-1 x^-1 = y x^-1; 7: x^-1 (x y) x = y x; 8: y (x y) y^-1 = y x;
        # 12, 13: conjugating y y by y changes nothing
        for m, w in want.items():
            self.assertEqual(a.apply(s, m), w, m)

    def test_inverse_moves(self):
        for s in (((X, Y), (Y, Y)), ((YI, XI, Y, X, X), (Y, X, YI)), a.TARGET, ((X,), (XI, Y))):
            for m in range(14):
                self.assertEqual(a.apply(a.apply(s, m), a.INV[m]), s, (s, m))

    def test_replay_limits(self):
        final, work, ok = a.replay(((X, Y), (Y,)), [3])
        self.assertEqual(final, a.TARGET)
        self.assertEqual(work, 3 + 2)
        self.assertTrue(ok)


class TestSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ball = a.build_ball(3)

    def test_ball(self):
        self.assertEqual(self.ball[a.TARGET], (0, None))
        # move 4: (x, y x); move 6 then gives x x x^-1 = x, so s = (x, y x), one move (5) away
        s = a.apply(a.apply(a.TARGET, 4), 6)
        self.assertEqual(s, ((X,), (Y, X)))
        self.assertEqual(self.ball[s][0], 1)
        self.assertEqual(a.replay(s, a.ball_path(self.ball, s))[0], a.TARGET)

    def test_bfs_exact(self):
        # <x, y | x y = 1; y = 1> is one move (3) from the target, and not the target itself
        path, proven, _ = a.bfs(((X, Y), (Y,)), self.ball, 3, 20000)
        self.assertEqual(path, [3])
        self.assertTrue(proven)
        # six moves out from the target: BFS with radius 3 and depth 3 finds a path of length <= 6
        s = a.TARGET
        for m in (4, 6, 2, 9, 1, 12):
            s = a.apply(s, m)
        path, proven, _ = a.bfs(s, self.ball, 3, 20000)
        self.assertIsNotNone(path)
        self.assertLessEqual(len(path), 6)
        self.assertTrue(proven)
        self.assertEqual(a.replay(s, path)[0], a.TARGET)
        # four moves out: the length found agrees with a plain breadth-first search from s
        s = a.TARGET
        for m in (4, 6, 2, 9):
            s = a.apply(s, m)
        path, proven, _ = a.bfs(s, self.ball, 3, 20000)
        self.assertTrue(proven)
        self.assertEqual(len(path), plain_distance(s, 4))

    def test_gs_and_shorten(self):
        s = a.TARGET
        for m in (4, 6, 2, 9, 1, 12, 5, 8, 3, 10):
            s = a.apply(s, m)
        path, _ = a.gs(s, self.ball, 50000, 10.0, 200)
        self.assertIsNotNone(path)
        self.assertEqual(a.replay(s, path)[0], a.TARGET)
        self.assertEqual(a.replay(s, a.shorten(s, path, self.ball))[0], a.TARGET)
        self.assertLessEqual(len(a.shorten(s, path, self.ball)), len(path))

    def test_submission_lines_and_chunks(self):
        rows = [{"challenge_id": "ac-00007", "path": [3], "replay_ok": True},
                {"challenge_id": "ms-train-0160", "path": [6, 4], "replay_ok": True},
                {"challenge_id": "ac-00008", "status": "NONE"}]
        self.assertEqual(a.submission_lines(rows), [
            "ac-00007: [3]", "sac-00007: [3, 16, 15]",
            "ms-train-0160: [6, 4]", "sac-train-0160: [6, 4, 16, 15]"])
        parts = a.chunks([str(i) for i in range(1201)])
        self.assertEqual([len(p) for p in parts], [500, 500, 201])


def plain_distance(s, limit):
    seen, layer = {s}, [s]
    for d in range(limit + 1):
        if a.TARGET in layer:
            return d
        nxt = []
        for t in layer:
            for m in range(14):
                u = a.apply(t, m)
                if u not in seen:
                    seen.add(u)
                    nxt.append(u)
        layer = nxt
    return None


@unittest.skipUnless(os.path.isdir(a.ROOT), "challenge repository not fetched")
class TestRepo(unittest.TestCase):
    def test_sample_paths_replay(self):
        starts = {cid: a.parse(d) for cid, d in
                  a.read_jsonl(a.repo_path("competition", "examples", "ac.jsonl"))}
        paths = {k: v for k, v in a.sample_paths().items() if k in starts}
        self.assertTrue(paths)
        for cid, path in paths.items():
            self.assertEqual(a.replay(starts[cid], path)[0], a.TARGET, cid)

    def test_parse_all(self):
        for name in (("problems", "ac.jsonl"), ("examples", "ac.jsonl")):
            for cid, d in a.read_jsonl(a.repo_path("competition", *name)):
                a.parse(d)


if __name__ == "__main__":
    unittest.main()
