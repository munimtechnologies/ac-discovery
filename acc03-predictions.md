# Job acc03: predictions (written 2026-10-27 ~16:30 UTC, before the jobs ran)

MV2 of Munim, Inc. Made with AI agents working in MV2's name. Text CC BY 4.0, code Apache-2.0.

## What acc02 found

acc02 (2026-10-27, 06:48 to 15:35 UTC, four shards on the Dell and the Blade; every graded check
held in all four) found paths for all 424 training presentations and for 4,934 of the 10,115 scored
ones (48.8%; by shard 1,184, 1,192, 1,316, 1,242). Every path was accepted by the challenge's
verifier as AC and as Stable AC, with the length the verifier reports. Pass A found 3,449 and pass B
1,485. Median path length by shard: 280, 273, 292, 299; longest 4,765. Each shard took 62 to 69
minutes, and peak memory was 0.40 to 0.54 GB.

Graded against acc02-predictions.md: every check held (65%): **held**. Training at least 418 (70%):
**held** (424). Scored at least 5% (70%), 15% (45%), 30% (25%): **held**; at least 50% (8%):
**missed** (48.8%). Pass A ahead of pass B (70%): **held**. Median length over 60 (60%): **held**.
Shards within 240 minutes and under 1.2 GB (85%): **held**. Smaller presentations solved more often
(start total at most 20 ahead of at least 30, 85%): **missed, and the other way round**: 487 of
1,342 (36.3%) with start total at most 20, 2,270 of 4,772 (47.6%) at 21 to 29, 2,177 of 4,001
(54.4%) at 30 or more.

Only the shortest verified path on a presentation scores (rules/discovery.md: the k teams tied for
the shortest each get 2^(1-k) points, every other team 0). acc02's paths are long and repeat the
same detours, so this job shortens them. Its searches stopped on their time caps (pop counts that
are multiples of 256, the interval of its clock check), so pass C gives the rest more time.

## What acc03 does

acc03.py re-runs acc02's passes A and B unchanged (fetched from this repository) on the same four
shards (index mod 4), then pass C on what they leave (--grow 8 --slack 32, 10 s and 3,000,000
nodes per presentation). acc03.c then shortens every path: for each state s_i of the path, every
state within 3 moves of it is looked up in a table of every state within 3 moves of a later state
s_j; a hit replaces the j - i moves between them by the d1 + d2 moves through the shared state when
that is shorter. Each replacement is replayed and compared with s_j before it is used; rounds
repeat until nothing is gained (at most 8). acc01's cut at the target's ball of radius 5 follows,
and acc01's moves must replay the shortened path to exactly (x, y), or the old path is kept.

## Graded checks (each must hold)

- Unit tests pass (test_acc03: 7 tests, including both builds and both C self-tests).
- Control: build and self-tests; 424 training presentations; no self-check failure; every training
  path replays, is accepted by the verifier with the training manifest at the reported length;
  no shortened path longer than before.
- Per shard: every presentation in the rows; no parse error; no self-check failure (the searches'
  replay, the Python replay and finish, the shortener: ERROR, no output, or a path acc01's moves do
  not replay); every path replays and is accepted as AC and Stable AC with the official manifest
  at the reported length; no path longer than before shortening.

## Predictions (MV2's agents' own estimates)

1. Every graded check holds in all four shards: 70% (acc03.c was written without a compiler at
   hand; a failed build or self-test shows up in the unit tests, the first step).
2. Solved, all four shards together, at least acc02's 4,934: 75% (passes A and B are time-capped,
   so a slower host can lose a few; pass C should more than make up for it).
3. Pass C solves at least 5% of what passes A and B leave: 55%; at least 15%: 20%.
4. Median length after shortening at most two thirds of the median before: 60%; at most half: 35%.
5. Total length of all paths cut by at least 25%: 60%.
6. At least 90% of the paths come back strictly shorter: 75%.
7. The share solved with start total at least 30 is again above the share at most 20: 80%.
8. Each shard finishes within 240 minutes: 70%. Peak memory under 1.8 GB: 80%.

## What happens next (decision rules)

- **A graded check fails:** nothing in that shard counts until it is explained; fix and re-run
  under a new version.
- **All checks hold:** acc02's and acc03's verified files both go to the leaderboard once MV2's
  SAIR registration is complete (a later, shorter path replaces a team's record). Next job: longer
  shortcuts (radius 4 from each state on the paths that are still longest) and a search that
  minimises path length rather than total relator length.
- **Shortening gains under 10% of total length:** the detours are not local; try exact
  breadth-first search between states further apart, and cyclic-class moves in reverse.
- Paths stay private until the challenge closes (2026-11-30); only counts and checks are published.
- Nothing here bears on the Andrews-Curtis conjecture itself, which remains open.
