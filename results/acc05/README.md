# Job acc05: four of eight shards graded (2026-10-28)

MV2 of Munim, Inc. Made with AI agents working in MV2's name. Text CC BY 4.0.

acc05 runs acc03's search on all 10,115 scored presentations of the SAIR / Caltech Andrews-Curtis
Conjecture Challenge, with acc04's radius-4 shortcut stages (s43, s44) on every path, in eight
shards (`acc05.py`, predictions in `acc05-predictions.md`, written before the job ran). Shards a0,
a1, b0 and b1 have finished. Shard d0 was stopped from outside the job (exit 143, a container stop,
not the code) and has been filed again unchanged; c0, c1 and d1 are still waiting for a machine.

**Every graded check held in all four shards** (12 each: build and C self-tests, shard size, no
parse or self-check error, every path replays to exactly (x, y), every path accepted by the
challenge's verifier as AC and as Stable AC with the verifier's length equal to ours, never longer
from stage to stage, no stage error).

    shard   solved          search total   s33 total   s43 total   s44 total   final median   minutes
    a0      721 / 1,265       354,157       244,773     223,502     213,038       192           165
    a1      737 / 1,264       359,530       247,438     226,403     216,231       193           165
    b0      683 / 1,265       296,448       202,689     186,183     178,724       182           190
    b1      683 / 1,264       269,929       185,083     170,232     163,512       181           181
    all   2,824 / 5,058     1,280,064       879,983     806,320     771,505

- s43 cut the s33 total by 8.4% and s44 a further 4.3%: **12.3% in all** (prediction 3, "at least
  10%" at 60%, holds so far).
- Every path reached s44 within the budget in all four shards (prediction 4 holds so far).
- Peak memory 0.90 to 1.03 GB (prediction 6 holds so far); every shard finished in under 200
  minutes (prediction 7 holds so far).
- Predictions 2 (total solved) and 5 (median of all paths) wait for the other four shards.

## What the leaderboard said

MV2's first 25 upload files (acc03's paths and acc04's shorter ones) were all accepted on
2026-10-28. The AC leaderboard read just after (updated 02:40 UTC) gave his team 29 scoring
challenges, against 5,508 and 5,542 for the two leading teams. Verification may still have been
running, but only the shortest verified path on a challenge scores, and a median of about 190
moves is very likely longer than the leaders' paths on most challenges. So acc05's files are
uploaded, and the next job (acc06, a pilot) tests a different search that minimises the number of
moves directly.

Paths are not published while the challenge runs; only counts. Finding paths for these
presentations says nothing about the Andrews-Curtis conjecture itself, which remains open.
