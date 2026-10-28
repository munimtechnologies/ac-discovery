# Job acc05: predictions (written 2026-10-28 ~02:30 UTC, before the job ran)

MV2 of Munim, Inc. Made with AI agents working in MV2's name. Text CC BY 4.0, code Apache-2.0.

The pilot acc04 (results/acc04) held every graded check. On the first 240 presentations of shard a,
radius-4 shortcuts cut the total length of acc03's paths by a further 12.0% (42,888 to 37,726
moves; stage s43 8.2%, then s44 4.2%), at a mean of 4.5 s and 6.8 s per path, peak memory 1.03 GB.
Its decision rule (at least 8% at most 30 s per path) says: run acc03's search again on all 10,115
presentations with both stages, in eight shards, and upload the results. acc05 does that: shards
a0 ... d1 are acc02's shards (index mod 4) split into every second presentation, 1,264 or 1,265
each, with a 240-minute budget from the start of each shard.

## Graded (each must hold, in every shard)

- Unit tests (3 in test_acc05); acc02's and acc03's builds and C self-tests.
- Every presentation of the shard accounted for; no parse error; no self-check error (acc03's
  has_error); no stage ERROR or BAD_REPLAY; at least one path found.
- Every path replays to exactly (x, y) within the limits, is accepted by the challenge's verifier as
  AC and as Stable AC, and the verifier's length equals ours.
- Never longer: final <= s43 <= s33 <= the search's path, for every path.

## Predictions (MV2's agents' own estimates)

1. Every graded check holds in all eight shards: 70%.
2. Solved in all eight shards together: between 5,602 and 5,830 (acc03's 5,716 plus or minus 2%;
   the searches stop on time caps, so load moves the count): 70%.
3. All eight shards together: s43 and s44 cut the s33 total by at least 10%: 60%; by at least 8%:
   80%.
4. Every path reaches s44 within the budget in every shard: 55%.
5. The median final length over all solved paths is at most 200 (acc03: 212 to 234 by shard): 60%.
6. Peak memory under 2 GB in every shard: 85%.
7. Each shard finishes in under 200 minutes: 65%.

## Decision rules

- **A graded check fails in a shard:** that shard's files are not uploaded until it is explained;
  the other shards' files are.
- **All checks hold:** upload every acc05 file after the acc03 files (a later, shorter verified path
  replaces the earlier record), then read the leaderboard. If MV2's scoring count is well below his
  solved count, length is still the lever: next a search that minimises the verifier's move count,
  or exact searches between path states 10 to 20 moves apart. If the scoring count is close to the
  solved count, the lever is count: more search time on the presentations no job has solved.
- **Paths not reached by s44 in some shard:** a follow-up job runs s44 on those only.

These counts say nothing about the Andrews-Curtis conjecture itself, which remains open.
