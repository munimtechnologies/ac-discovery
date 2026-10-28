# Job acc06 (beam pilot): graded 2026-10-28

MV2 of Munim, Inc. Made with AI agents working in MV2's name. Text CC BY 4.0, code Apache-2.0.
Counts only: paths and per-presentation lengths stay private until the SAIR / Caltech
Andrews-Curtis Conjecture Challenge closes (2026-11-30). Nothing here says anything about the
Andrews-Curtis conjecture itself, which remains open.

## What ran

`acc06.c` keeps, at every level of the verifier's own 14 moves, the `--width` states with the
smallest total relator length, and stops when a kept state lands in the radius-5 ball around
(x, y); a path found at level L has exactly L moves. Three widths (1k, 8k, 64k; 15, 30 and 45 s per
presentation) ran on the first 240 presentations of acc05's shard a0, and every path was then cut
by acc03's s33 shortcuts and compared with acc05a0's final lengths on the same presentations
(142 solved there). Job `acc06-ac-beam-v1`, 2 CPUs, 143 minutes, peak memory 0.75 GB.
Files: `acc06_grade.json` (the grader's output) and `stdout.log`.

## Graded checks: all 13 held

Unit tests, both C self-tests, all 240 presentations accounted for, no parse/beam/s33 error, every
final path replays to (x, y) and is accepted by the challenge's own verifier as AC and as Stable
AC with the official manifest at the length we computed, every "better" path accepted, and s33
never lengthened a beam path.

## Numbers

| | w1k | w8k | w64k |
|---|---|---|---|
| solved (of 240) | 51 | 80 | 70 |
| median length after s33 | 135 | 115 | 67 |
| shorter than acc05a0 (where both solved) | 22 of 51 | 63 of 80 | 62 of 70 |
| total after s33 / acc05a0's total, same presentations | 107% | 82% | 60% |

- Any width solved 86 presentations, all of them also solved by acc05a0; none that acc05a0 missed.
- On those 86, the shortest beam path totals 9,691 moves against acc05a0's 14,708 (-34%), and it is
  strictly shorter on 78. Over all 142 that acc05a0 solved, the best of the two totals 37,368
  against 42,781: **-12.6%**.
- The widest beam ran out of time, not states: every one of the 170 presentations w64k left
  unsolved stopped at its 45 s limit, after 102 to 224 levels. The narrower beams mostly ran their
  full 600 levels without a path, so for them the beam itself was the limit.
- The width that gave the shortest path: w64k on 57 presentations, w8k on 26, w1k on 3.

## Predictions (written before the job; acc06-predictions.md)

| # | Prediction | Outcome |
|---|---|---|
| 1 | every graded check holds (70%) | held |
| 2 | w64k total at most 70% of acc05a0's where both solved (50%); at most 85% (70%) | held: 60% |
| 3 | shortest strictly shorter on at least 71 of the 142 (60%) | held: 78 |
| 4 | at least one presentation acc05a0 missed is solved (50%) | failed: 0 |
| 5 | wider is better on the presentations all three solved (65%) | not graded: the grader did not compute that common set; w64k gave the shortest path on 57 of 86 |
| 6 | w64k solves at least 120 of the 142 (45%) | failed: 70 |
| 7 | peak memory under 2 GB (85%) | held: 0.75 GB |

## Decision

The combined cut (12.6%) falls in the 10-25% band of acc06's rules: no bulk beam over all 10,115
presentations yet. The 78 shorter paths (156 AC and Stable AC lines, all verifier-accepted) are
uploaded, and the second pilot, job acc07 (`acc07.py`, `acc07-predictions.md`), gives the 64k beam
240 s on 80 presentations it left unsolved, to see whether time was the limit. A read of MV2's
own "Scoring challenges" table on the leaderboard after the upload decides whether beam lengths
reach the best-known lengths at all; on the challenges where MV2 already scores, the best-known
paths are 8-26 moves, tied by 30-40 teams.
