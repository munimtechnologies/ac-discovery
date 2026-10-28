# Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Unit tests for acc07.py (job acc07, acc07-predictions.md). Needs acc01.py to acc06.py next to it,
the challenge repository unpacked by acc01's fetch, acc07_items.json and ref_acc05a0.json.
Expectations worked out by hand from acc06's rows (2026-10-28):

- 80 items: 56 that acc05a0 solved and acc06 did not ("ref"), 24 that neither solved ("unsolved"),
  all among the first 240 of shard a0, in its order: first ac-00001 (unsolved), last ac-01897.
- every "ref" item has an acc05a0 length (ac-00033: 183, ac-01441: 37); no "unsolved" item has one.
- grade on an empty folder must not raise, and must fail pilot_ran and items.
"""
import argparse
import tempfile
import unittest

import acc06
import acc07


class TestPilot(unittest.TestCase):
    def test_items(self):
        items, group = acc07.load_items()
        ids = [cid for cid, _ in items]
        self.assertEqual(len(ids), 80)
        self.assertEqual(len(set(ids)), 80)
        self.assertEqual(sum(group[c] == "ref" for c in ids), 56)
        self.assertEqual(sum(group[c] == "unsolved" for c in ids), 24)
        self.assertEqual((ids[0], ids[-1]), ("ac-00001", "ac-01897"))
        first = {cid for cid, _ in acc06.items_of(240)}
        self.assertTrue(set(ids) <= first)

    def test_ref(self):
        items, group = acc07.load_items()
        ref = acc06.load_ref()
        for cid, _ in items:
            self.assertEqual(cid in ref, group[cid] == "ref", cid)
        self.assertEqual((ref["ac-00033"], ref["ac-01441"]), (183, 37))

    def test_config(self):
        name, opts = acc07.CONFIG
        self.assertEqual(opts[opts.index("--width") + 1], "64000")
        self.assertEqual(opts[opts.index("--seconds") + 1], "240")

    def test_grade_empty(self):
        with tempfile.TemporaryDirectory() as d:
            g = acc07.grade(argparse.Namespace(n=80, out_dir=d))["graded"]
            self.assertFalse(g["pilot_ran"] or g["items"])


if __name__ == "__main__":
    unittest.main()
