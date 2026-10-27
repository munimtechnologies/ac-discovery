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
- `acc03.c`, `acc03.py`: job acc03 (queued). acc02's search again, a third pass with more time on
  what it leaves, and a path shortener in C: from each state of a path, every state within 3 moves
  is looked up in a table of the states within 3 moves of later states of the same path, and a
  hit replaces the moves in between when that is shorter. Each replacement is replayed before it
  is used, and the whole path is replayed again in Python and checked by the verifier.
- `test_acc0N.py`, `acc0N-predictions.md`: unit tests, and what we expected, written before each
  job ran.
- `results/acc01/`, `results/acc02/`: graded checks and counts (no paths).

## Results so far

    job    presentations   paths found      checked by the verifier (AC and Stable AC)
    acc01  424 training    418              all
    acc01  10,115 scored   180 (1.8%)       all; 2 proven shortest (length 8), median 35 moves
    acc02  424 training    424              all
    acc02  10,115 scored   4,934 (48.8%)    all; median length 273 to 299 by shard, longest 4,765

acc02 ran on 2026-10-27 in four shards of about 65 minutes each (two processes each). Searching
classes of states instead of explicit moves took it from 180 to 4,934 presentations, but its
paths are long, because rotating a relator by conjugation costs one move per letter. Only the
shortest verified path on a presentation scores, so acc03 shortens them.

One finding we did not expect: larger presentations fell more often. With a starting total length
of at most 20, acc02 solved 487 of 1,342 (36.3%); at 21 to 29, 2,270 of 4,772 (47.6%); at 30 or
more, 2,177 of 4,001 (54.4%). We had predicted the opposite (acc02-predictions.md, prediction 6).

The paths themselves are not published here while the challenge runs: it keeps paths private
until it closes and then releases all valid solutions as a public benchmark. Counts and checks
are published as jobs finish.

Finding paths for these presentations says nothing about the Andrews-Curtis conjecture itself,
which remains open.

## Licence

Apache-2.0 (see LICENSE). The challenge repository is also Apache-2.0.
