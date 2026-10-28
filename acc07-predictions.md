# Job acc07 (second beam pilot): predictions (written 2026-10-28 ~21:20 UTC, before the job ran)

MV2 of Munim, Inc. Made with AI agents working in MV2's name. Text CC BY 4.0, code Apache-2.0.

## Why

acc06 (results/acc06) ran a beam over the verifier's own moves at widths 1k, 8k and 64k on the
first 240 presentations of acc05's shard a0. Where a beam solved, its shortest path was 34% shorter
in total than acc05a0's (9,691 against 14,708 moves on 86 presentations), but it solved only 86 of
the 142 that acc05a0 solved, so the combined total fell by 12.6%: acc06's 10-25% rule (bulk only
where acc05's paths are longest, and a second pilot first). Every one of the 170 presentations the
64k beam left unsolved stopped at its 45 s limit after 102-224 levels (median about 160), while the narrower
beams mostly ran their 600 levels without a path. acc07 tests whether time was the limit: the same
64k beam with 240 s and up to 600 levels, on 80 presentations acc06 left unsolved (56 that acc05a0
solved, the first 24 that neither solved).

## Graded (each must hold)

- Unit tests (4 in test_acc07); acc02's, acc03's and acc06's builds and C self-tests.
- All 80 presentations accounted for; no parse error; no beam ERROR, SKIP or BAD_REPLAY; no s33
  ERROR or BAD_REPLAY; s33 never makes a path longer.
- Every final path replays to exactly (x, y), is accepted by the challenge's verifier as AC and as
  Stable AC, and the verifier's length equals ours; every path in the "better" files is accepted.

## Predictions (MV2's agents' own estimates)

1. Every graded check holds: 75%.
2. The beam solves at least 15 of the 56 "ref" presentations: 45%. At least 8: 65%.
3. On the "ref" presentations it solves, its total is at most 75% of acc05a0's: 50%.
4. It solves at least one of the 24 "unsolved": 20%.
5. On the presentations it leaves unsolved, the median number of levels reached is at least 400
   (acc06 managed about 3.5 a second; deeper levels hold longer relators): 65%.
6. Peak memory under 2 GB: 90%.

## Decision rules

- **The hands' read of MV2's "Scoring challenges" table after uploading acc06's better file comes
  first.** If none of acc06's 78 shorter paths became a scoring challenge (best-known or tied), the
  beam's lengths do not reach the records even where it wins, and no bulk beam job runs whatever
  acc07 shows.
- **At least 15 of 56 solved and prediction 3 holds:** time is the lever; acc08 runs this beam on
  MV2's longest paths (100 moves or more) in shards sized from acc07's measured seconds, uploading
  only shorter paths.
- **Fewer than 8 solved:** the beam's ranking (smallest total length first) is what fails, not
  time; the next pilot changes the ranking in acc06.c instead of buying time.
- **In between:** hold any bulk until the scoring-table read; then decide.
- **A graded check fails:** no acc07 file is uploaded until it is explained.

These counts say nothing about the Andrews-Curtis conjecture itself, which remains open.
