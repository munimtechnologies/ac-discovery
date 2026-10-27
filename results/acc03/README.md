# acc03 results (counts only, no paths)

MV2 of Munim, Inc., 2026-10-27. Made with AI agents working in MV2's name. Text CC BY 4.0.

Shards a and b have finished. Shards c and d (the other half of the 10,115 scored presentations)
have not finished yet, and this page will be updated when they do. Every graded check held in both
finished shards (18 of 18 each): the build and both C self-tests, the 424 training presentations
as a control, the three search passes, the shortener, acc01's replay of every shortened path,
and the challenge's verifier on every path as AC and as Stable AC, with the official manifest, at
the length the verifier reports.

    shard  host   scored  solved  pass A  pass B  pass C  acc02 solved  minutes  peak GB
    a      Dell   2,529   1,393   873     322     198     1,184         185      0.92
    b      Blade  2,529   1,469   877     477     115     1,192         169      1.04
    a+b           5,058   2,862   1,750   799     313     2,376

Path lengths before and after the shortener (the same paths, solved presentations only):

    shard  median before  median after  total before  total after  shorter          longest after
    a      303            212           621,267       424,488      1,389 of 1,393   2,972
    b      306            218           692,728       476,524      1,464 of 1,469   3,509

The shortener cut the total length by 31.7% (a) and 31.2% (b), and the median by 30% and 29%.
On the 424 training presentations it cut the total from 11,019 to 8,047 moves (median 20 to 14).
Time per shard: passes A, B and C took 949, 2,927 and 6,396 s (a) and 905, 2,830 and 5,407 s (b),
shortening 685 and 759 s.

Solved by starting total length:

    start total   shard a             shard b
    at most 20    132 / 342   (39%)   124 / 322   (39%)
    21 to 29      633 / 1,180 (54%)   695 / 1,213 (57%)
    30 or more    628 / 1,007 (62%)   650 / 994   (65%)

Graded against acc03-predictions.md, so far on two shards of four: every check held in every
shard (70%): held in a and b, c and d pending. Solved at least acc02's 4,934 (75%): pending (a and
b alone found 2,862, 486 more than acc02 on the same two shards). Pass C at least 5% of what A and
B leave (55%): held (198 of 1,334 and 115 of 1,175, 12.5% together); at least 15% (20%): missed.
Median after shortening at most two thirds of before (60%): missed (0.70 and 0.71); at most half
(35%): missed. Total length cut by at least 25% (60%): held. At least 90% strictly shorter (75%):
held (99.7%). Start total 30 or more solved more often than 20 or less (80%): held. Each shard
within 240 minutes (70%) and under 1.8 GB (80%): held.

Only the shortest verified path on a presentation scores in the Discovery Track, so a 30% cut
matters only where another team's path is not shorter still. These counts say nothing about the
Andrews-Curtis conjecture itself, which remains open.
