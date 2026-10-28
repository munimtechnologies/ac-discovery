# Job acc04: radius-4 shortcuts (pilot), graded

MV2 of Munim, Inc., 2026-10-28. Made with AI agents working in MV2's name. Text CC BY 4.0.

Job acc04-ac-radius4-v1 ran from 01:01 to 01:34 UTC on 2026-10-28 (2 CPUs, peak memory 1.03 GB).
Predictions and decision rules were written before it ran (../../acc04-predictions.md). It took
acc03's search and shortener ("s33": radius 3 on both sides) and added two stages of acc03.c on
every path: s43 (radius 4 from each path state, radius 3 around later states) and s44 (radius 4 on
both sides, tables up to 16,000,000 entries). Counts only; no paths are published while the
challenge runs.

## Results

    set                       solved     total length: search -> s33 -> s43 -> s44        cut s33 -> s44
    training (424)            424 / 424  11,019 -> 8,047 -> 7,767 -> 7,612                 5.4%
    scored, first 240 of a    132 / 240  60,893 -> 42,888 -> 39,361 -> 37,726              12.0%

On the scored set, s43 made 114 of the 132 paths strictly shorter and s44 then 97; the median path
went from 218 (s33) to 198 to 192 moves, and the longest from 2,972 to 2,320. Mean time per path:
4.5 s at s43 (longest 39 s) and 6.8 s at s44 (longest 54 s); every path reached both stages well
inside the budget. Every final path replays to (x, y), and the challenge's verifier accepted all of
them as AC (and, on the scored set, as Stable AC) with the same length as ours. The scored set's
search solved 132 of its 240 presentations (55%), in line with acc03's 56.5% overall.

## Graded against the predictions

- Every graded check holds in both sets (80%): held (10 checks on training, 11 on scored).
- Scored: s43 + s44 cut the s33 total by at least 5% (50%): held; by at least 10% (20%): held
  (12.0%).
- Scored: s44 cuts the s43 total by at least 2% (40%): held (4.2%).
- Scored: at least half of the paths strictly shorter at s43 (55%): held (114 of 132).
- Training: the s33 total falls by less than 5% more (70%): **missed** (5.4%).
- Scored: s44 reaches every path within the budget (60%): held; mean s44 time at most 30 s (55%):
  held (6.8 s).
- Peak memory under 2.5 GB (80%): held (1.03 GB).

## Decision

The rule for a cut of at least 8% at no more than 30 s per path applies: job acc05 runs acc03's
search again on all 10,115 presentations in eight shards with both radius-4 stages, and its files
are uploaded after acc03's (a later, shorter verified path replaces the earlier one). Predictions in
../../acc05-predictions.md.

Files: acc04_train_grade.json, acc04_scored_grade.json, acc04_stdout.log.
