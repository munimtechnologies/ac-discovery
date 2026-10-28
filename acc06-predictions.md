# Job acc06 (pilot): predictions (written 2026-10-28 ~08:30 UTC, before the job ran)

MV2 of Munim, Inc. Made with AI agents working in MV2's name. Text CC BY 4.0, code Apache-2.0.

## Why

MV2's first 25 upload files to the SAIR Andrews-Curtis challenge (acc03's paths for all four
shards, acc04's shorter ones) were accepted on 2026-10-28, but the leaderboard read just after gave
him 29 scoring challenges, against 5,508 (Bluepug) and 5,542 (memcon.ai) for the leading teams on
the AC board. Verification may still have been running, but only the shortest verified path on a
challenge scores, and MV2's paths are long: a median of 181 to 193 moves after acc05's radius-4
stages (four of eight shards graded, every check held). acc02.c ranks relator pairs up to rotation
and pays for the rotations afterwards; acc03.c only removes local detours. acc06.c searches the
verifier's own moves level by level and keeps the --width shortest states, so a path found at level
L has exactly L moves. This pilot measures whether that gives shorter paths, at three widths, on
the first 240 presentations of acc05's shard a0, against acc05a0's final lengths there (142 solved).

## Graded (each must hold)

- Unit tests (4 in test_acc06); acc02's, acc03's and acc06's builds and C self-tests.
- All 240 presentations accounted for; no parse error; no beam ERROR, SKIP or BAD_REPLAY (Python
  replay of acc06.c's path); no s33 ERROR or BAD_REPLAY; at least one path found.
- Every final path replays to exactly (x, y) within the limits, is accepted by the challenge's
  verifier as AC and as Stable AC, and the verifier's length equals ours; every path in the
  "better" files is accepted too.
- s33 never makes a beam path longer.

## Predictions (MV2's agents' own estimates)

1. Every graded check holds: 70%.
2. On the presentations that both w64k and acc05a0 solved, w64k's total length after s33 is at most
   70% of acc05a0's: 50%. At most 85%: 70%.
3. The shortest path over the three widths is strictly shorter than acc05a0's on at least half of
   the 142 presentations acc05a0 solved: 60%.
4. At least one presentation acc05a0 did not solve is solved by some width: 50%.
5. Wider is better: on the presentations all three widths solved, total length after s33 is
   w64k <= w8k <= w1k: 65%.
6. w64k solves at least 120 of the 142 that acc05a0 solved: 45%.
7. Peak memory under 2 GB: 85%.

## Decision rules

- **Best-of-widths cuts the combined total (min of acc06 and acc05a0 per presentation, over the 142)
  by at least 25%:** a bulk job runs the best width (or the two best) on all 10,115 presentations
  in shards, with only paths shorter than MV2's earlier ones uploaded.
- **Cut between 10% and 25%:** bulk only on the presentations where acc05's paths are longest, and
  try a wider beam or a second ranking (cyclically reduced length) in a second pilot.
- **Cut under 10%:** the beam is not the lever; next is the count of solved presentations (more
  search time on the ~4,300 unsolved, and Stable AC moves for the Stable AC board).
- **New solves (prediction 4) at 5% or more of the 98 unsolved:** run the beam on every unsolved
  presentation as well.
- **A graded check fails:** no acc06 file is uploaded until it is explained.

These counts say nothing about the Andrews-Curtis conjecture itself, which remains open.
