# Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Unit tests for acc02.py and acc02.c (job acc02). Needs acc01.py next to it and gcc. The paths
and states below were worked out by hand with acc01's move table (move 2: r0 -> r0 r1, move 3:
r0 -> r0 r1^-1, move 0: r0 -> r0^-1); the small presentations were built from (x, y) by explicit
moves, so each is AC-trivial."""
import unittest

import acc01
import acc02

X, Y = 1, 2


class TestHelpers(unittest.TestCase):
    def test_to_str(self):
        self.assertEqual(acc02.to_str((1, -1, 2, -2)), "xXyY")
        self.assertEqual(acc02.to_str(()), "-")

    def test_parse_line(self):
        r = acc02.parse_line("ac-00001 SOLVED 10 20 3 0.010 3,6,13\n")
        self.assertEqual((r["id"], r["status"], r["pops"], r["stored"], r["moves"], r["path"]),
                         ("ac-00001", "SOLVED", 10, 20, 3, [3, 6, 13]))
        self.assertEqual(acc02.parse_line("ac-00002 NONE 5 9 0 1.000 -")["path"], [])

    def test_cut_loops(self):
        start = ((X, Y), (Y,))
        # move 2 gives (x y y, y) and move 3 takes it back: the loop goes
        self.assertEqual(acc02.cut_loops(start, [2, 3, 0]), [0])
        self.assertEqual(acc02.cut_loops(start, [0, 0, 3]), [3])
        self.assertEqual(acc02.cut_loops(start, [3]), [3])

    def test_finish(self):
        ball = acc01.build_ball(3)
        start = ((X, Y), (Y,))
        self.assertEqual(acc02.finish(start, [3], ball), ([3], "OK"))
        # (y, x): two single letters, but not the target; the ball or the search must finish it
        full, how = acc02.finish(((Y,), (X,)), [], acc01.build_ball(5))
        self.assertEqual(how, "OK")
        self.assertEqual(acc01.replay(((Y,), (X,)), full)[0], acc01.TARGET)
        self.assertEqual(acc02.finish(start, [2], ball), (None, "BAD_REPLAY"))


class TestSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.built, cls.tail = acc02.build()

    def test_build_and_selftest(self):
        self.assertTrue(self.built, self.tail)

    def test_small_presentations(self):
        self.assertTrue(self.built, self.tail)
        starts = {"t1": ((X, Y, X), (Y, X)),
                  "t2": ((X, Y, X, -Y, -X), (X, Y)),
                  "t3": ((X, Y, X, -Y, -X), (X, Y, X, Y, -X, -Y, -X))}
        ball = acc01.build_ball(5)
        for name, opts in acc02.PASSES:
            got = acc02.run_c(starts, opts + ["--seconds", "2"], 2, 100000)
            self.assertEqual(sorted(got), sorted(starts))
            for cid, start in starts.items():
                self.assertEqual(got[cid]["status"], "SOLVED", (name, cid))
                full, how = acc02.finish(start, got[cid]["path"], ball)
                self.assertEqual(how, "OK", (name, cid))
                self.assertEqual(acc01.replay(start, full)[0], acc01.TARGET)

    def test_too_long_is_skipped(self):
        self.assertTrue(self.built, self.tail)
        long_word = tuple([X, Y] * 40)            # 80 letters, over acc02.c's MAXL of 64
        got = acc02.run_c({"t": (long_word, (Y,))}, ["--seconds", "1"], 1, 1000)
        self.assertEqual(got["t"]["status"], "SKIP")


if __name__ == "__main__":
    unittest.main()
