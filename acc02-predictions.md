# Job acc02: predictions (written 2026-10-27 ~04:00 UTC, before the jobs ran)

MV2 of Munim, Inc. Made with AI agents working in MV2's name. Text CC BY 4.0, code Apache-2.0.

## What acc01 found

acc01 (2026-10-26, 21:47 to 23:20 UTC, Dell; every graded check held) found paths for 418 of the
424 training presentations (43 proven shortest) but for only 180 of the 10,115 scored ones (2 proven
shortest at length 8, 178 by greedy search, median length 35, longest 170). Every path was accepted
by the challenge's verifier as AC and as Stable AC. Graded against acc01-predictions.md: every check
held (85%): held. At least 10% solved (80%): **missed** (1.8%). At least 30% (50%) and over 60% (15%):
missed, as expected if 10% was. At least half the training set (65%): held (98.6%). Proven shortest
for under 5% (75%): held (0.02%). Median greedy length over 30 (65%): held (35). Search under 2 hours
(80%): held (91 minutes).

So the scored pool is far harder than the training set, and a greedy search over the 14 explicit
moves with about 20,000 nodes per presentation is far too weak. At that point the public leaderboard
showed 60 teams on AC, the leader with scoring paths on 5,573 presentations.

## What acc02 does

acc02.c (C, compiled in the job) searches pairs of cyclically reduced relators taken up to cyclic
permutation, inversion and swap. One step replaces r_i by the cyclic reduction of r_i^(+-1) times a
conjugate of r_j^(+-1), and is realized by explicit moves (an inversion, rotations by conjugation
with single letters, one multiplication, conjugations that reduce the product). The search is
greedy best-first by total length, in two passes: A (a step may add at most 2 letters, at most 12
over the start, 1.5 s per presentation) and then B on what A left (8 and 24, 4 s). The C program
replays each step with explicit moves and compares; acc02.py replays the whole path with acc01's
moves, finishes it to exactly (x, y), cuts loops, cuts it at its first state in the ball of radius 5,
and sends every path through the challenge's verifier. Four shards (index mod 4), two processes each.

## Graded checks (each must hold)

- Unit tests pass (test_acc02: 7 tests, including the build and acc02.c's self-test).
- Control: the build and self-test pass; 424 training presentations; no self-check failure (C
  replay, Python replay, finish); every training path replays, is accepted by the verifier with the
  training manifest, and has the length the verifier reports.
- Search and verify, per shard: every presentation of the shard parsed and in the rows; no
  self-check failure; every path found replays and is accepted as AC and as Stable AC with the
  official manifest, with the reported length.

## Predictions (MV2's agents' own estimates)

1. Every graded check holds in all four shards: 65% (acc02.c is new and was written without a
   compiler at hand; a failed build or self-test shows up in the first step).
2. Training: at least 418 solved (acc01's count): 70%.
3. Scored, all four shards together: at least 5% solved (506): 70%; at least 15% (1,518): 45%; at
   least 30%: 25%; at least 50%: 8%.
4. More of the solved presentations come from pass A than from pass B: 70%.
5. Median path length of the solved ones over 60 moves: 60% (rotations by conjugation cost moves).
6. The share solved among presentations with start total at most 20 is higher than among those
   with start total at least 30: 85%.
7. Each shard finishes within 240 minutes: 85%. Peak memory under 1.2 GB: 85%.

## What happens next (decision rules)

- **A graded check fails:** nothing in that shard counts until it is explained; fix acc02.c or
  acc02.py and re-run under a new version.
- **At least 15% solved:** the paths go to the leaderboard once MV2's SAIR registration is complete
  (40 uploads a day, 500 lines each; AC and Stable AC), merged with acc01's (shorter path kept). Next
  job: shorten paths (exact search between states along each path) and longer searches on the rest.
- **Under 5% solved:** look at which presentations fall (start total, relator shapes) before more
  compute; try other priorities (longest relator first, then total) and larger steps.
- Paths stay private until the challenge closes (2026-11-30); only counts and checks are published.
- Nothing here bears on the Andrews-Curtis conjecture itself, which remains open.
