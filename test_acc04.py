# Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Unit tests for acc04.py (job acc04, acc04-predictions.md). Needs acc01.py, acc02.py, acc02.c,
acc03.py and acc03.c next to it, and gcc. Expectations worked out by hand:

- P = [2, 4, 8, 13] from (x, y), then P undone ([12, 9, 5, 3]), ends where it started, so radius 4
  on both sides must return the empty path (the undo is 4 moves, inside one radius-4 ball).
- A deadline already passed: acc04's runner kills acc03.c and returns only complete lines, so it
  may return nothing, but never a line whose path length differs from its "new" field.
- apply_stage keeps a strictly shorter replaying path, records the stage length, and marks a row
  the stage never reached as NOT_REACHED with its earlier path and length.
"""
import time
import unittest

import acc01
import acc03
import acc04

P = [2, 4, 8, 13]
UNDO = [acc01.INV[m] for m in reversed(P)]


class TestStages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ok, cls.tail = acc03.build()

    def test_build(self):
        self.assertTrue(self.ok, self.tail)

    def test_radius_four_cuts_the_undo(self):
        self.assertEqual(UNDO, [12, 9, 5, 3])
        got = acc04.run_short_until({"t": (acc01.TARGET, P + UNDO)}, 1, acc04.STAGES[1][1],
                                    time.time() + 600)["t"]
        self.assertEqual((got["status"], got["old"], got["new"], got["path"]), ("OK", 8, 0, []))

    def test_passed_deadline_returns_only_whole_lines(self):
        jobs = {f"t{k}": (acc01.TARGET, P + UNDO) for k in range(40)}
        got = acc04.run_short_until(jobs, 2, acc04.STAGES[0][1], time.time() - 1)
        for r in got.values():
            self.assertEqual(len(r["path"]), r["new"])

    def test_apply_stage(self):
        ball = acc01.build_ball(1)
        rows = [{"challenge_id": "a", "path": P + UNDO, "length": 8, "replay_ok": True},
                {"challenge_id": "b", "path": P + UNDO, "length": 8, "replay_ok": True},
                {"challenge_id": "c", "status": "NONE"}]
        got = {"a": {"id": "a", "status": "OK", "old": 8, "new": 0, "rounds": 1, "seconds": 0.5,
                     "path": []}}
        acc04.apply_stage(rows, {"a": acc01.TARGET, "b": acc01.TARGET}, "s43", got, ball)
        self.assertEqual((rows[0]["path"], rows[0]["length"], rows[0]["s43_length"],
                          rows[0]["s43_status"]), ([], 0, 0, "OK"))
        self.assertEqual((rows[1]["length"], rows[1]["s43_length"], rows[1]["s43_status"]),
                         (8, 8, "NOT_REACHED"))
        self.assertNotIn("s43_length", rows[2])

    def test_stage_stats(self):
        found = [{"s33_length": 10, "s43_length": 8, "s43_seconds": 1.0, "s43_status": "OK"},
                 {"s33_length": 6, "s43_length": 6, "s43_status": "NOT_REACHED"}]
        st = acc04.stage_stats(found, "s43", "s33")
        self.assertEqual((st["sum"], st["shorter_than_prev"], st["seconds_mean"]), (14, 1, 1.0))


if __name__ == "__main__":
    unittest.main()
