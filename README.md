# ac-discovery

MV2's searches for the Discovery Track of the
[Andrews-Curtis Conjecture Challenge](https://github.com/SAIRcompetition/Andrews-Curtis)
(SAIR Foundation and Caltech; organised by Sergei Gukov, Terence Tao and Lucas Fagan; deadline
2026-11-30). The challenge asks for short sequences of AC moves that take each of 10,115 balanced
presentations `<x, y | r0 = 1; r1 = 1>` of the trivial group to exactly `(x, y)`.

By MV2 of Munim, Inc. (mv2@munimtech.com). The code and notes were researched and written with AI
agents working in MV2's name; the challenge welcomes AI tools.

## What is here

- `acc01.py`: job acc01, a first pass. An exact meet-in-the-middle search proves shortest paths of
  length up to 8, and a greedy best-first search by total relator length (the baseline of
  Shehper et al., [arXiv:2408.15332](https://arxiv.org/abs/2408.15332)) covers the rest. Every
  path is replayed and then checked by the challenge's own verifier.
- `test_acc01.py`, `acc01-predictions.md`: its unit tests, and what we expected before it ran.
- `results/acc01/`: its graded checks and counts (no paths).
- `acc02.c`, `acc02.py`: job acc02 (queued). A greedy best-first search in C over pairs of
  cyclically reduced relators taken up to cyclic permutation and inversion: one step multiplies a
  relator by any conjugate of the other (or its inverse), and is turned back into explicit moves
  of the verifier's move set. Every step is replayed in C, every path again in Python, and then
  checked by the challenge's verifier.
- `test_acc02.py`, `acc02-predictions.md`: its unit tests, and what we expect, written before the
  jobs ran.

## Results so far

    job    presentations   paths found   checked by the verifier (AC and Stable AC)
    acc01  424 training    418           all
    acc01  10,115 scored   180 (1.8%)    all; 2 proven shortest (length 8), median 35 moves

acc01 ran on 2026-10-26 (91 minutes, two processes, about 1 s per presentation). The scored pool
is far harder than the training set: a greedy search over the 14 explicit moves spends its nodes
on conjugates of the same state, which is what acc02 changes.

The paths themselves are not published here while the challenge runs: it keeps paths private
until it closes and then releases all valid solutions as a public benchmark. Counts and checks
are published as jobs finish.

Finding paths for these presentations says nothing about the Andrews-Curtis conjecture itself,
which remains open.

## Licence

Apache-2.0 (see LICENSE). The challenge repository is also Apache-2.0.
