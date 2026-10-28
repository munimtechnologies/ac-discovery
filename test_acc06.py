# Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Unit tests for acc06.py (job acc06, acc06-predictions.md). Needs acc01.py to acc05.py next to it
and the challenge repository unpacked by acc01's fetch. Expectations worked out by hand:

- acc05's shard a0 is every presentation with index = 0 mod 8, so its first 240 are ac-00001,
  ac-00009, ..., ac-01913 (1 + 8 * 239).
- ref_acc05a0.json holds the 142 of those 240 that acc05a0 solved (its rows, read 2026-10-28), so
  every key is one of the 240 IDs.
- parse_beam on a line of acc06.c's output format.
- grade on an empty folder must not raise, and must fail pilot_ran, items and some_solved.
"""
import argparse
import tempfile
import unittest

import acc06


class TestPilot(unittest.TestCase):
    def test_items(self):
        ids = [cid for cid, _ in acc06.items_of(240)]
        self.assertEqual(len(ids), 240)
        self.assertEqual((ids[0], ids[1], ids[-1]), ("ac-00001", "ac-00009", "ac-01913"))

    def test_ref(self):
        ref = acc06.load_ref()
        ids = {cid for cid, _ in acc06.items_of(240)}
        self.assertEqual(len(ref), 142)
        self.assertTrue(set(ref) <= ids)
        self.assertEqual((ref["ac-00009"], ref["ac-01913"]), (91, 450))

    def test_parse_beam(self):
        r = acc06.parse_beam("ac-00009 SOLVED 3 2 0.125 3,7,12\n")
        self.assertEqual((r["id"], r["status"], r["length"], r["levels"], r["path"]),
                         ("ac-00009", "SOLVED", 3, 2, [3, 7, 12]))
        r = acc06.parse_beam("ac-00001 NONE 0 300 45.002 -\n")
        self.assertEqual((r["status"], r["path"]), ("NONE", []))

    def test_grade_empty(self):
        with tempfile.TemporaryDirectory() as d:
            g = acc06.grade(argparse.Namespace(n=240, out_dir=d))["graded"]
            self.assertFalse(g["pilot_ran"] or g["items"] or g["some_solved"])


if __name__ == "__main__":
    unittest.main()
