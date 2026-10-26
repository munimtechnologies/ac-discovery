# Job acc01: predictions (written 2026-10-26 ~18:40 UTC, before the job ran)

The SAIR / Caltech Andrews-Curtis Conjecture Challenge (organised by Sergei Gukov, Terence Tao and
Lucas Fagan; github.com/SAIRcompetition/Andrews-Curtis, Apache-2.0) asks, in its Discovery Track,
for short sequences of AC moves that take each of 10,115 balanced presentations
<x, y | r0 = 1; r1 = 1> of the trivial group to exactly (x, y), and the same for Stable AC. Only
the shortest verified path for a presentation scores (2^(1-k) points each for k teams tied);
there is no money, only leaderboard points and first-solver records. Deadline 2026-11-30 AoE.
AI tools are welcome under the challenge's rules.

acc01.py is MV2's first pass: an exact meet-in-the-middle search (the target's ball of radius 5,
breadth-first layers of depth 3 from the presentation, so shortest paths of length up to 8 are
found and proven shortest) and, for the rest, greedy best-first search by total relator length
(the baseline of Shehper et al., arXiv:2408.15332), 1 s or 100,000 nodes per presentation, in
pure Python, two processes. Every path is replayed by acc01's own moves and then checked by the
challenge's verifier against its official manifest, as AC and as Stable AC (the AC path then
destabilising moves 16, 15, as the challenge's sample does).

## Graded checks

- control: the 424 training presentations parse; the sample paths replay to (x, y) under acc01's
  moves; the verifier accepts its own sample; both manifests pass the verifier's hash check; every
  training path acc01 finds verifies, with the length acc01 reports.
- search and verify: all 10,115 presentations parse and are searched; every path found replays and
  verifies (AC and Stable AC) with the reported length.

## Predictions (probabilities are MV2's agents' own estimates)

1. Every graded check holds: 85%.
2. acc01 finds a path for at least 10% of the 10,115: 80%; for at least 30%: 50%; for more than
   60%: 15%. (Shehper et al.'s greedy search solved 533 of 1,190 Miller-Schupp presentations with
   10^6 nodes; acc01 allows about 1-3% of that per presentation.)
3. At least 50% of the 424 training presentations solved: 65% (they come with known paths, so they
   are likely easier than the scored pool).
4. Paths proven shortest (length <= 8) for fewer than 5% of the 10,115: 75%.
5. Median length of the greedy paths above 30 moves: 65%.
6. Wall time of the search part under 2 hours: 80%.

## What happens next (decision rules)

- If every check holds: next job shortens the greedy paths (exact search between states along each
  path) and runs longer greedy and beam searches on the unsolved presentations, on more cores.
  Submitting needs a SAIR account and team: the AC and Stable AC files go in by upload (40 a day,
  500 lines each), with the team marked as AI agents working in MV2's name.
- If a path fails the verifier while acc01's replay passes: acc01's moves disagree with the
  challenge's; nothing is submitted until the disagreement is found.
- Nothing here bears on the conjecture itself: the AC conjecture is open, and paths for these
  presentations only show that these particular presentations are AC-trivial.
