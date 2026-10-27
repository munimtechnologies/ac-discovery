# Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Unit tests for acc03.py and acc03.c (job acc03, acc03-predictions.md). Needs acc01.py, acc02.py
and acc02.c next to it, and gcc. Expectations worked out by hand:

- P = [2, 4, 8, 13] from (x, y), then P undone ([12, 9, 5, 3], INV of P reversed), ends where it
  started, so the shortener must return the empty path.
- Moves 6 then 7 conjugate r0 by x and then by x^-1: a loop of two moves, which must go.
- A random walk of 200 moves (fixed seed; totals kept at most 40) has immediate back-steps with
  probability about 1/14 per move, so it must come back strictly shorter, and acc01's moves must
  take the shortened path to the same end state as the walk (the C moves agree with acc01's).
"""
import random
import unittest

import acc01
import acc03

P = [2, 4, 8, 13]
UNDO = [acc01.INV[m] for m in reversed(P)]


def end(start, path):
    return acc01.replay(start, path)[0]


class TestShortener(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ok, cls.tail = acc03.build()

    def test_build_and_selftests(self):
        self.assertTrue(self.ok, self.tail)
        self.assertIn("SELFTEST ok", self.tail)

    def test_undo_is_cut_to_nothing(self):
        self.assertEqual(UNDO, [12, 9, 5, 3])
        self.assertEqual(end(acc01.TARGET, P + UNDO), acc01.TARGET)
        got = acc03.run_short({"t": (acc01.TARGET, P + UNDO)}, 1)["t"]
        self.assertEqual((got["status"], got["old"], got["new"], got["path"]), ("OK", 8, 0, []))

    def test_two_move_loop_is_cut(self):
        start = ((1, 2, -1, -2, 1), (2, 2, 1))
        path = P[:2] + [6, 7] + P[2:]
        got = acc03.run_short({"u": (start, path)}, 1)["u"]
        self.assertEqual(got["status"], "OK")
        self.assertLessEqual(got["new"], 4)
        self.assertEqual(end(start, got["path"]), end(start, P))

    def test_random_walk_agrees_with_acc01(self):
        rnd = random.Random(20261027)
        start = ((1, 2, 1, -2, -1, -2), (2, 1, 1, 2))
        s, path = start, []
        while len(path) < 200:
            m = rnd.randrange(14)
            t = acc01.apply(s, m)
            if acc01.total(t) <= 40:
                s = t
                path.append(m)
        got = acc03.run_short({"w": (start, path)}, 2)["w"]
        self.assertEqual(got["status"], "OK")
        self.assertLess(got["new"], 200)
        self.assertEqual(len(got["path"]), got["new"])
        self.assertEqual(end(start, got["path"]), s)


class TestRows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        acc03.build()

    def test_parse_short(self):
        self.assertEqual(acc03.parse_short("ac-00001 OK 10 4 2 0.010 2,3,4,5\n"),
                         {"id": "ac-00001", "status": "OK", "old": 10, "new": 4, "rounds": 2,
                          "seconds": 0.01, "path": [2, 3, 4, 5]})
        self.assertEqual(acc03.parse_short("t OK 8 0 2 0.001 -")["path"], [])

    def test_shorten_rows_keeps_the_shorter(self):
        ball = acc01.build_ball(1)
        rows = [{"challenge_id": "t", "path": P + UNDO, "length": 8, "replay_ok": True},
                {"challenge_id": "n", "status": "NONE"}]
        acc03.shorten_rows(rows, {"t": acc01.TARGET}, 1, ball)
        r = rows[0]
        self.assertEqual((r["path"], r["length"], r["orig_length"], r["short_status"]),
                         ([], 0, 8, "OK"))
        self.assertNotIn("path", rows[1])

    def test_has_error_and_bucket(self):
        self.assertFalse(acc03.has_error({"status": "SOLVED", "A_status": "SOLVED",
                                          "short_status": "OK"}))
        self.assertFalse(acc03.has_error({"status": "SOLVED", "short_status": "LONG"}))
        self.assertTrue(acc03.has_error({"status": "NONE", "C_status": "ERROR"}))
        self.assertTrue(acc03.has_error({"status": "SOLVED", "short_status": "BAD_REPLAY"}))
        self.assertEqual([acc03.bucket(t) for t in (9, 20, 21, 29, 30, 40)],
                         ["le20", "le20", "21_29", "21_29", "ge30", "ge30"])


if __name__ == "__main__":
    unittest.main()
