# Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Unit tests for acc05.py (job acc05, acc05-predictions.md). Needs acc01.py to acc04.py next to it
and the challenge repository unpacked by acc01's fetch. Expectations worked out by hand:

- 10,115 = 4 * 2,528 + 3, so acc02's shards a, b, c hold 2,529 presentations and d holds 2,528
  (acc03a graded "of": 2,529). Every second one from position 0 or 1: a, b, c split 1,265 + 1,264
  and d 1,264 + 1,264; the eight halves hold each of the 10,115 challenge IDs exactly once.
- grade on an empty folder must not raise, and must fail run_ran, shard_size and some_solved.
"""
import argparse
import tempfile
import unittest

import acc02
import acc05


class TestShards(unittest.TestCase):
    def test_half_sizes(self):
        want = {"a": (1265, 1264), "b": (1265, 1264), "c": (1265, 1264), "d": (1264, 1264)}
        for s, (h0, h1) in want.items():
            self.assertEqual((len(acc05.items_of(s, 0)), len(acc05.items_of(s, 1))), (h0, h1), s)

    def test_eight_halves_partition(self):
        ids = [cid for s in acc02.SHARDS for h in acc05.HALVES for cid, _ in acc05.items_of(s, h)]
        self.assertEqual(len(ids), 10115)
        self.assertEqual(len(set(ids)), 10115)

    def test_grade_empty(self):
        with tempfile.TemporaryDirectory() as d:
            args = argparse.Namespace(shard="b", half=1, out_dir=d)
            self.assertEqual(acc05.tag_of(args), "acc05b1")
            g = acc05.grade(args)["graded"]
            self.assertFalse(g["run_ran"] or g["shard_size"] or g["some_solved"])


if __name__ == "__main__":
    unittest.main()
