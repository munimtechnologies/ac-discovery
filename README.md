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
- `test_acc01.py`: unit tests. The moves are checked on words worked out by hand from the
  verifier's move table, and the sample paths are replayed on the training presentations.
- `acc01-predictions.md`: what we expected, written before the job ran.

The paths themselves are not published here while the challenge runs: it keeps paths private
until it closes and then releases all valid solutions as a public benchmark. Counts and checks
will be published as jobs finish.

Finding paths for these presentations says nothing about the Andrews-Curtis conjecture itself,
which remains open.

## Licence

Apache-2.0 (see LICENSE). The challenge repository is also Apache-2.0.
