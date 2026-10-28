# ac-discovery

MV2's searches for the Discovery Track of the
[Andrews-Curtis Conjecture Challenge](https://github.com/SAIRcompetition/Andrews-Curtis)
(SAIR Foundation and Caltech; organised by Sergei Gukov, Terence Tao and Lucas Fagan; deadline
2026-11-30). The challenge asks for short sequences of AC moves that take each of 10,115 balanced
presentations `<x, y | r0 = 1; r1 = 1>` of the trivial group to exactly `(x, y)`.

By MV2 of Munim, Inc. (mv2@munimtech.com). The code and notes were researched and written with AI
agents working in MV2's name.

## What is here

- `acc01.py`: job acc01, a first pass. An exact meet-in-the-middle search proves shortest paths of
  length up to 8, and a greedy best-first search by total relator length (the baseline of
  Shehper et al., [arXiv:2408.15332](https://arxiv.org/abs/2408.15332)) covers the rest. Every
  path is replayed and then checked by the challenge's own verifier.
- `acc02.c`, `acc02.py`: job acc02. A greedy best-first search in C over pairs of cyclically
  reduced relators taken up to cyclic permutation and inversion: one step multiplies a relator by
  any conjugate of the other (or its inverse), and is turned back into explicit moves of the
  verifier's move set. Every step is replayed in C, every path again in Python, and then checked
  by the challenge's verifier.
- `acc03.c`, `acc03.py`: job acc03. acc02's search again, a third pass with more time on what it
  leaves, and a path shortener in C: from each state of a path, every state within 3 moves is
  looked up in a table of the states within 3 moves of later states of the same path, and a hit
  replaces the moves in between when that is shorter. Each replacement is replayed before it is
  used, and the whole path is replayed again in Python and checked by the verifier.
- `acc04.py`: job acc04, a pilot. It measures what radius 4 adds to acc03's shortener, and what it
  costs, on the training presentations and on 240 scored ones, before any bulk run.
- `test_acc0N.py`, `acc0N-predictions.md`: unit tests, and what we expected, written before each
  job ran.
- `results/acc01/`, `results/acc02/`, `results/acc03/`: graded checks and counts (no paths).

## Results so far

    job    presentations       paths found      checked by the verifier (AC and Stable AC)
    acc01  424 training        418              all
    acc01  10,115 scored       180 (1.8%)       all; 2 proven shortest (length 8), median 35 moves
    acc02  424 training        424              all
    acc02  10,115 scored       4,934 (48.8%)    all; median length 273 to 299 by shard, longest 4,765
    acc03  424 training        424              all; total length 11,019 -> 8,047 after shortening
    acc03  10,115 scored       5,716 (56.5%)    all; median length 212 to 234 by shard after
                                                shortening, total length cut by 31.4%
    acc04  pilot               queued

acc02 ran on 2026-10-27 in four shards of about 65 minutes each (two processes each). Searching
classes of states instead of explicit moves took it from 180 to 4,934 presentations, but its
paths are long, because rotating a relator by conjugation costs one move per letter. Only the
shortest verified path on a presentation scores, so acc03 shortens them. acc03 (four shards of
about three hours, 2026-10-27/28) solved 782 more presentations than acc02 (its third pass found
599 paths that its first two passes had not), and its shortener made 99.7% of the paths strictly
shorter.

One finding we did not expect: larger presentations fell more often. With a starting total length
of at most 20, acc03 solved 515 of 1,342 (38.4%); at 21 to 29, 2,636 of 4,772 (55.2%); at 30 or
more, 2,565 of 4,001 (64.1%). acc02 showed the same pattern (36.3%, 47.6%, 54.4%), against our
prediction (acc02-predictions.md, prediction 6).

The paths themselves are not published here while the challenge runs: it keeps paths private
until it closes and then releases all valid solutions as a public benchmark. Counts and checks
are published as jobs finish.

Finding paths for these presentations says nothing about the Andrews-Curtis conjecture itself,
which remains open.

## Licence

Apache-2.0 (see LICENSE). The challenge repository is also Apache-2.0.
