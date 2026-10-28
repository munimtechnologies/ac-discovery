# Job acc04 (pilot): predictions (written 2026-10-28 ~01:30 UTC, before the job ran)

MV2 of Munim, Inc. Made with AI agents working in MV2's name. Text CC BY 4.0, code Apache-2.0.

acc03 finished all four shards on 2026-10-27/28 with every graded check held: 5,716 of the 10,115
scored presentations solved (acc02: 4,934), and its radius-3 shortener ("r3/r3") cut total path
length by 31.2% to 31.7% per shard (medians 303 -> 212, 306 -> 218, 311 -> 222, 331 -> 234). The
leaders of the challenge's leaderboard score on about 5,500 presentations each, about as many as
acc03 solves, so whether MV2's paths score depends on their length. acc04 measures what radius 4
adds (stage s43: r1 = 4, r2 = 3; then stage s44: r1 = 4, r2 = 4) on the 424 training presentations
and on the first 240 presentations of shard a, and what it costs, before any bulk job.

## Graded (each must hold, in both sets)

- Unit tests (5 in test_acc04); acc02's and acc03's builds and C self-tests.
- Every presentation accounted for (424 and 240); no parse error; no self-check error (acc03's
  has_error); no stage ERROR or BAD_REPLAY.
- Every final path replays to exactly (x, y) within the limits, is accepted by the challenge's
  verifier as AC (and as Stable AC on the scored set), and the verifier's length equals ours.
- Never longer: final <= s43 <= s33 <= the search's path, for every path.

## Predictions (MV2's agents' own estimates)

1. Every graded check holds in both sets: 80%.
2. Scored set: s43 and s44 together cut the s33 total by at least 5%: 50%; at least 10%: 20%.
3. Scored set: s44 cuts the s43 total by at least 2%: 40%.
4. Scored set: at least half of the solved paths get strictly shorter at s43: 55%.
5. Training set: the s33 total (8,047 in acc03) falls by less than 5% more: 70%.
6. Scored set: s44 reaches every path within the 120-minute budget: 60%; mean s44 time per path
   at most 30 s: 55%.
7. Peak memory under 2.5 GB: 80%.

## Decision rules

- **A graded check fails:** nothing from acc04 is used until it is explained.
- **s43 + s44 cut at least 8% at a mean of at most 30 s per path:** acc05 re-runs acc03's search in
  eight shards with both stages and the results are uploaded; the shorter path replaces the record.
- **Less than 3%:** local shortcuts are used up. The next lever is a search that minimises verifier
  moves (rotations included), or exact searches between path states 10 to 20 moves apart, chosen
  with the first leaderboard numbers.
- **In between:** use only the cheaper of the two stages that gives most of the gain.

These counts say nothing about the Andrews-Curtis conjecture itself, which remains open.
